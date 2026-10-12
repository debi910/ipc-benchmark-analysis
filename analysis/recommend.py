#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

WEIGHTS = {"p99": 0.4, "cpu": 0.4, "ctx": 0.2}


def load(path: str) -> pd.DataFrame:
    data = pd.read_csv(path, skipinitialspace=True)
    data["mech"] = data["mech"].str.strip()
    return data[data["status"].str.strip() == "ok"].copy()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="results/raw.csv")
    parser.add_argument("--size", type=int, required=True)
    parser.add_argument("--pattern", choices=["pingpong", "stream"], required=True)
    parser.add_argument("--goal", choices=["min_latency", "max_throughput", "min_cpu", "balanced"], required=True)
    parser.add_argument("--max-p99-us", type=float)
    parser.add_argument("--top", type=int, default=3)
    args = parser.parse_args()
    data = load(args.input)
    data = data[data["mode"] == args.pattern].copy()
    data["distance"] = (data["size_bytes"].apply(lambda x: abs(__import__("math").log(max(x, 1)) - __import__("math").log(args.size))))
    data = data.sort_values("distance").groupby("mech", as_index=False).first()
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
    print(data.head(args.top)[["mech", "size_bytes", metric]].to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
