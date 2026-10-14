#!/usr/bin/env python3
"""Build the self-contained static results dashboard."""
from __future__ import annotations

import argparse
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

import recommend

MECHANISMS = ["pipe", "fifo", "mq", "uds", "shm_spin", "shm_futex", "shm_hybrid"]
METRICS = {
    "p50": "p50_ns", "p99": "p99_ns", "throughput": "mb_per_s",
    "cpu_msg": "cpu_ns_per_msg", "cpu": "cpu_pct", "ctx": "ctx_per_msg",
}


def load(path: str) -> pd.DataFrame:
    data = recommend.load(path)
    numeric = [c for c in data.columns if c not in
               {"git_commit", "mech", "mode", "pin", "status", "chunked"}]
    data[numeric] = data[numeric].apply(pd.to_numeric, errors="coerce")
    data["cpu_ns_per_msg"] = (data["cpu_user_s"] + data["cpu_sys_s"]) * 1e9 / data["iters"]
    return data


def aggregate(data: pd.DataFrame) -> list[dict]:
    fields = ["p50_ns", "p90_ns", "p99_ns", "p999_ns", "mb_per_s",
              "cpu_pct", "cpu_ns_per_msg", "ctx_per_msg", "iters"]
    grouped = data.groupby(["mech", "mode", "pin", "size_bytes"], as_index=False)
    rows = []
    for keys, group in grouped:
        med = group[fields].median()
        row = dict(zip(["mech", "mode", "pin", "size_bytes"], keys))
        for field in fields:
            row[field] = float(med[field])
            row[field + "_min"] = float(group[field].min())
            row[field + "_max"] = float(group[field].max())
        rows.append(row)
    return rows


def recommendations(data: pd.DataFrame) -> dict:
    result = {}
    for mode in ("pingpong", "stream"):
        result[mode] = {}
        subset = recommend.aggregate(data[data["pin"] == "cross"])
        subset = subset[subset["mode"] == mode]
        for size in sorted(subset["size_bytes"].unique()):
            result[mode][str(int(size))] = {}
            for goal in ("min_latency", "max_throughput", "min_cpu", "balanced"):
                ranked = recommend.rank(recommend.interpolate(subset, int(size)), goal)
                result[mode][str(int(size))][goal] = [
                    {"mech": str(row.mech), "score": float(row.score),
                     "p50_ns": float(row.p50_ns), "p99_ns": float(row.p99_ns),
                     "cpu_ns_per_msg": float(row.cpu_ns_per_msg),
                     "ctx_per_msg": float(row.ctx_per_msg)}
                    for _, row in ranked.head(3).iterrows()
                ]
    return result


def git_commit(data: pd.DataFrame) -> str:
    values = [str(v).strip() for v in data["git_commit"].dropna().unique() if str(v).strip()]
    if values:
        return values[0]
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="results/raw.csv")
    parser.add_argument("--output", default="docs/index.html")
    parser.add_argument("--chart", default="vendor/chart.umd.min.js")
    args = parser.parse_args()
    data = load(args.input)
    payload = aggregate(data)
    meta = {
        "commit": git_commit(data), "rows": int(len(data)),
        "generated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "sizes": sorted({int(v) for v in data["size_bytes"].unique()}),
        "mechanisms": MECHANISMS,
        "method": "WSL2/virtualised; five cross-core repetitions; three same-core repetitions",
        "animation_factor": 100000,
        "same_spin_iters": int(data[(data["mech"] == "shm_spin") &
                                    (data["pin"] == "same")]["iters"].median()),
    }
    template = Path(__file__).with_name("dashboard_template.html").read_text()
    chart = re.sub(r"/\*.*?\*/", "", Path(args.chart).read_text(), flags=re.S).strip()
    replacements = {
        "__CHART__": chart,
        "__DATA__": json.dumps(payload, separators=(",", ":")),
        "__META__": json.dumps(meta, separators=(",", ":")),
        "__RECS__": json.dumps(recommendations(data), separators=(",", ":")),
    }
    for marker, value in replacements.items():
        if marker == "__CHART__":
            value = json.dumps(value, separators=(",", ":"))
        template = template.replace(marker, value.replace("</script>", "<\\/script>"))
    Path(args.output).write_text(template)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
