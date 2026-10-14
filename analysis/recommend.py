#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
import math
import warnings

WEIGHTS = {"p99": 0.4, "cpu": 0.4, "ctx": 0.2}


def load(path: str) -> pd.DataFrame:
    data = pd.read_csv(path, skipinitialspace=True)
    data.columns = data.columns.astype(str).str.strip()
    for column in data.columns[data.dtypes == "string"].tolist() + data.columns[data.dtypes == "object"].tolist():
        if column in data:
            data[column] = data[column].astype(str).str.strip()
    return data[data["status"].astype(str).str.strip() == "ok"].copy()


def interpolate(data: pd.DataFrame, size: int) -> pd.DataFrame:
    rows = []
    for mech, group in data.groupby("mech"):
        group = group.sort_values("size_bytes")
        if size < group["size_bytes"].min() or size > group["size_bytes"].max():
            warnings.warn("requested size is outside measured range; clamping to nearest measurement")
            row = group.iloc[0] if size < group["size_bytes"].min() else group.iloc[-1]
            rows.append(row)
            continue
        exact = group[group["size_bytes"] == size]
        if not exact.empty:
            rows.append(exact.iloc[0]); continue
        lower = group[group["size_bytes"] < size].iloc[-1]
        upper = group[group["size_bytes"] > size].iloc[0]
        weight = (math.log(size) - math.log(lower["size_bytes"])) / (
            math.log(upper["size_bytes"]) - math.log(lower["size_bytes"]))
        row = lower.copy()
        row["size_bytes"] = size
        for column in ("p50_ns", "p99_ns", "mb_per_s", "cpu_user_s", "ctx_per_msg"):
            if column in row:
                row[column] = math.exp(math.log(max(lower[column], 1e-12)) +
                                       weight * (math.log(max(upper[column], 1e-12)) -
                                                 math.log(max(lower[column], 1e-12))))
        rows.append(row)
    return pd.DataFrame(rows)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="results/raw.csv")
    parser.add_argument("--export-rules", action="store_true")
    parser.add_argument("--size", type=int)
    parser.add_argument("--pattern", choices=["pingpong", "stream"])
    parser.add_argument("--goal", choices=["min_latency", "max_throughput", "min_cpu", "balanced"])
    parser.add_argument("--max-p99-us", type=float)
    parser.add_argument("--pin", choices=["cross", "same"], default="cross")
    parser.add_argument("--top", type=int, default=3)
    args = parser.parse_args()
    if args.export_rules:
        data = load(args.input)
        data = data[data["pin"] == "cross"]
        rows = []
        for size in sorted(data["size_bytes"].unique()):
            for pattern in ("pingpong", "stream"):
                for goal in ("min_latency", "max_throughput", "min_cpu", "balanced"):
                    subset = interpolate(data[data["mode"] == pattern], int(size),)
                    metric = {"min_latency": "p50_ns", "max_throughput": "mb_per_s",
                              "min_cpu": "cpu_user_s", "balanced": "p50_ns"}[goal]
                    if goal == "balanced":
                        for col in ("p99_ns", "cpu_user_s", "ctx_per_msg"):
                            low, high = subset[col].min(), subset[col].max()
                            subset[col + "_n"] = (subset[col] - low) / (high - low or 1)
                        subset["score"] = (WEIGHTS["p99"] * subset["p99_ns_n"] +
                                           WEIGHTS["cpu"] * subset["cpu_user_s_n"] +
                                           WEIGHTS["ctx"] * subset["ctx_per_msg_n"])
                        winner = subset.sort_values("score").iloc[0]
                    else:
                        winner = subset.sort_values(metric, ascending=goal != "max_throughput").iloc[0]
                    rows.append((size, pattern, goal, winner["mech"]))
        text = ["# Recommendation table", "", "| Size | Pattern | Goal | Recommended mechanism |", "|---:|---|---|---|"]
        text += [f"| {s} | {p} | {g} | {m} |" for s, p, g, m in rows]
        Path("results/recommendation_table.md").write_text("\n".join(text) + "\n")
        return 0
    if args.size is None or args.pattern is None or args.goal is None:
        parser.error("--size, --pattern, and --goal are required unless --export-rules is used")
    data = load(args.input)
    data = data[data["mode"] == args.pattern].copy()
    data = data[data["pin"] == args.pin].copy()
    data = interpolate(data, args.size)
    if args.max_p99_us is not None and "p99_ns" in data:
        data = data[data["p99_ns"] <= args.max_p99_us * 1000]
    metric = {"min_latency": "p50_ns", "max_throughput": "mb_per_s",
              "min_cpu": "cpu_user_s", "balanced": "p50_ns"}[args.goal]
    if args.goal == "balanced":
        for col in ("p99_ns", "cpu_user_s", "ctx_per_msg"):
            low, high = data[col].min(), data[col].max()
            data[col + "_n"] = (data[col] - low) / (high - low or 1)
        data["score"] = (WEIGHTS["p99"] * data["p99_ns_n"] +
                         WEIGHTS["cpu"] * data["cpu_user_s_n"] +
                         WEIGHTS["ctx"] * data["ctx_per_msg_n"])
        data = data.sort_values("score")
    else:
        data = data.sort_values(metric, ascending=args.goal != "max_throughput")
    print("Measured-machine recommendation (WSL2 results; not a universal ranking)")
    print(data.head(args.top)[["mech", "size_bytes", metric]].to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
