#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
import math
import warnings

WEIGHTS = {"p99": 0.4, "cpu": 0.4, "ctx": 0.2}
BALANCED_COMPONENTS = ("p99_ns", "cpu_ns_per_msg", "ctx_per_msg")


def load(path: str) -> pd.DataFrame:
    data = pd.read_csv(path, skipinitialspace=True)
    data.columns = data.columns.astype(str).str.strip()
    for column in data.columns[data.dtypes == "string"].tolist() + data.columns[data.dtypes == "object"].tolist():
        if column in data:
            data[column] = data[column].astype(str).str.strip()
    return data[data["status"].astype(str).str.strip() == "ok"].copy()


def aggregate(data: pd.DataFrame) -> pd.DataFrame:
    data = data.copy()
    for column in ("size_bytes", "iters", "p50_ns", "p99_ns", "cpu_user_s",
                   "cpu_sys_s", "ctx_per_msg", "mb_per_s"):
        if column in data:
            data[column] = pd.to_numeric(data[column], errors="coerce")
    data["cpu_ns_per_msg"] = (
        (data["cpu_user_s"] + data["cpu_sys_s"]) * 1e9 / data["iters"]
    )
    keys = ["mech", "mode", "pin", "size_bytes"]
    return data.groupby(keys, as_index=False).median(numeric_only=True)


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
        for column in ("p50_ns", "p99_ns", "mb_per_s", "cpu_ns_per_msg", "ctx_per_msg"):
            if column in row:
                row[column] = math.exp(math.log(max(lower[column], 1e-12)) +
                                       weight * (math.log(max(upper[column], 1e-12)) -
                                                 math.log(max(lower[column], 1e-12))))
        rows.append(row)
    return pd.DataFrame(rows)


def balanced_rank(data: pd.DataFrame) -> pd.DataFrame:
    """Return rows ranked by the documented min-max balanced score."""
    data = data.dropna(subset=list(BALANCED_COMPONENTS)).copy()
    for component in BALANCED_COMPONENTS:
        low = data[component].min()
        high = data[component].max()
        data[component + "_n"] = (
            (data[component] - low) / (high - low) if high != low else 0.0
        )
    data["score"] = (
        WEIGHTS["p99"] * data["p99_ns_n"]
        + WEIGHTS["cpu"] * data["cpu_ns_per_msg_n"]
        + WEIGHTS["ctx"] * data["ctx_per_msg_n"]
    )
    return data.sort_values(["score", "mech"], kind="stable").reset_index(drop=True)


def rank(data: pd.DataFrame, goal: str) -> pd.DataFrame:
    if goal == "balanced":
        return balanced_rank(data)
    metric = {
        "min_latency": "p50_ns",
        "max_throughput": "mb_per_s",
        "min_cpu": "cpu_ns_per_msg",
    }[goal]
    ranked = data.dropna(subset=[metric]).copy()
    ranked["score"] = ranked[metric] if goal != "max_throughput" else -ranked[metric]
    return ranked.sort_values(["score", "mech"], kind="stable").reset_index(drop=True)


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
    parser.add_argument("--exclude", default="")
    args = parser.parse_args()
    if args.export_rules:
        data = load(args.input)
        data = data[data["pin"] == "cross"]
        data = aggregate(data)
        rows = []
        for size in sorted(data["size_bytes"].unique()):
            for pattern in ("pingpong", "stream"):
                for goal in ("min_latency", "max_throughput", "min_cpu", "balanced"):
                    subset = interpolate(data[data["mode"] == pattern], int(size),)
                    ranked = rank(subset, goal)
                    rows.append((size, pattern, goal,
                                 ranked.iloc[0]["mech"] if not ranked.empty else "unavailable"))
        text = ["# Recommendation table", "", "| Size | Pattern | Goal | Recommended mechanism |", "|---:|---|---|---|"]
        text += [f"| {s} | {p} | {g} | {m} |" for s, p, g, m in rows]
        Path("results/recommendation_table.md").write_text("\n".join(text) + "\n")
        return 0
    if args.size is None or args.pattern is None or args.goal is None:
        parser.error("--size, --pattern, and --goal are required unless --export-rules is used")
    data = load(args.input)
    data = data[data["mode"] == args.pattern].copy()
    data = data[data["pin"] == args.pin].copy()
    excluded = {item.strip() for item in args.exclude.split(",") if item.strip()}
    if excluded:
        data = data[~data["mech"].isin(excluded)]
    data = aggregate(data)
    data = interpolate(data, args.size)
    if args.max_p99_us is not None and "p99_ns" in data:
        data = data[data["p99_ns"] <= args.max_p99_us * 1000]
    data = rank(data, args.goal)
    if data.empty:
        parser.error("no complete rows are available for this goal and selection")
    print("Measured-machine recommendation (WSL2 results; not a universal ranking)")
    print("Caveat: CPU ranking is measured under back-to-back load; spin variants keep "
          "approximately two cores busy (measured cpu_pct approximately 194%) even "
          "at low message rates.")
    columns = ["mech", "size_bytes", "p50_ns", "p99_ns", "cpu_ns_per_msg",
               "ctx_per_msg", "score"]
    print(data.head(args.top)[columns].to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
