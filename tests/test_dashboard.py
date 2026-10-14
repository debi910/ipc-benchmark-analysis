import json
import random
import re
import subprocess
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent


def build_dashboard(path):
    subprocess.run(
        [sys.executable, "analysis/make_dashboard.py", "--input", "results/raw.csv",
         "--output", str(path), "--chart", "vendor/chart.umd.min.js"],
        cwd=ROOT, check=True,
    )


def embedded(path, name):
    text = path.read_text()
    if name == "DATA":
        match = re.search(r"const DATA=(.*?),META=", text, re.S)
    else:
        match = re.search(r",META=(.*?),RECS=", text, re.S)
    assert match
    return json.loads(match.group(1))


def test_dashboard_builds_without_external_resources(tmp_path):
    output = tmp_path / "index.html"
    build_dashboard(output)
    text = output.read_text()
    assert output.stat().st_size > 200_000
    assert "http://" not in text
    assert "https://" not in text


def test_dashboard_row_count_and_random_medians(tmp_path):
    output = tmp_path / "index.html"
    build_dashboard(output)
    data = embedded(output, "DATA")
    meta = embedded(output, "META")
    assert meta["rows"] == 413

    raw = pd.read_csv(ROOT / "results/raw.csv")
    raw["cpu_ns_per_msg"] = (raw["cpu_user_s"] + raw["cpu_sys_s"]) * 1e9 / raw["iters"]
    fields = ["p50_ns", "p90_ns", "p99_ns", "p999_ns", "mb_per_s",
              "cpu_pct", "cpu_ns_per_msg", "ctx_per_msg", "iters"]
    expected = raw.groupby(["mech", "mode", "pin", "size_bytes"])[fields].median()
    random.seed(413)
    for row in random.sample(data, 10):
        key = (row["mech"], row["mode"], row["pin"], row["size_bytes"])
        for field in fields:
            values = raw.set_index(["mech", "mode", "pin", "size_bytes"]).loc[key, field]
            actuals = [row[field], row[field + "_min"], row[field + "_max"]]
            expected_values = [expected.loc[key, field], values.min(), values.max()]
            for actual, expected_value in zip(actuals, expected_values):
                assert (pd.isna(actual) and pd.isna(expected_value)) or actual == expected_value
