#!/usr/bin/env python3
import argparse
import csv
import math
import sys
import json
from collections import Counter
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("csv_path", nargs="?", default="results/raw.csv")
    args = parser.parse_args()
    path = Path(args.csv_path)
    rows = list(csv.DictReader(path.open()))
    for row in rows:
        for key, value in list(row.items()):
            if isinstance(value, str):
                row[key] = value.strip()
    warnings = []
    errors = []
    if not rows:
        errors.append("no data rows")
    for index, row in enumerate(rows, 2):
        if row.get(None):
            errors.append(f"row {index} has extra CSV fields")
        for key in ("size_bytes", "iters", "wall_s", "msgs_per_s", "mb_per_s"):
            if row[key] == "":
                continue
            value = float(row[key])
            if not math.isfinite(value) or value < 0:
                errors.append(f"row {index} has invalid {key}")
        if row["status"] != "ok":
            warnings.append(f"row {index} status={row['status']}")
        if row["mode"] == "pingpong" and row["p50_ns"] and float(row["p50_ns"]) > float(row["p99_ns"]):
            errors.append(f"row {index} p50 > p99")
        if row["mode"] == "stream" and row["wall_s"] and abs(float(row["msgs_per_s"]) * float(row["wall_s"]) - int(row["iters"])) > 1:
            warnings.append(f"row {index} throughput differs from iters/wall")
    counts = Counter((r["mech"].strip(), r["mode"], r["size_bytes"]) for r in rows)
    if any(count > 1 for count in counts.values()):
        warnings.append("duplicate mechanism/mode/size combinations found")
    if len(rows) and sum(r["status"] != "ok" for r in rows) / len(rows) > 0.05:
        errors.append("more than 5% of rows are not ok")
    if len(rows) < 42:
        warnings.append(f"only {len(rows)} rows present; full matrix is not present")
    if rows and any("wsl" in str(r).lower() for r in rows[:1]):
        warnings.append("WSL/virtualised environment detected")
    info_path = path.parent / "system_info.json"
    if info_path.exists() and json.loads(info_path.read_text()).get("env") == "wsl2":
        warnings.append("WSL/virtualised environment detected")
    for warning in warnings:
        print(f"WARNING: {warning}")
    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
