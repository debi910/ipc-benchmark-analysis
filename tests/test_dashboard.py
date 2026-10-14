import json
import random
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parent.parent


def build_dashboard(path):
    subprocess.run(
        [sys.executable, "analysis/make_dashboard.py", "--input", "results/raw.csv",
         "--output", str(path), "--chart", "vendor/chart.umd.min.js"],
        cwd=ROOT, check=True,
    )


def node_command():
    node = shutil.which("node")
    if node:
        return [node]
    windows_node = Path("/mnt/c/Program Files/nodejs/node.exe")
    if windows_node.exists():
        return [str(windows_node)]
    return None


def windows_path(path, node):
    if node[0].endswith(".exe") and Path("/mnt/c").exists():
        return subprocess.check_output(["wslpath", "-w", str(path)], text=True).strip()
    return str(path)


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


def test_inline_scripts_pass_node_check(tmp_path):
    node = node_command()
    if node is None:
        pytest.skip("node is not installed; install Node.js to run inline syntax checks")
    output = tmp_path / "index.html"
    build_dashboard(output)
    scripts = re.findall(r"<script(?: [^>]*)?>(.*?)</script>", output.read_text(), re.S)
    assert scripts
    for index, script in enumerate(scripts, 1):
        script_path = tmp_path / f"dashboard-script-{index}.js"
        script_path.write_text(script)
        result = subprocess.run(
            node + ["--check", windows_path(script_path, node)],
            capture_output=True, text=True,
        )
        assert result.returncode == 0, result.stderr


def test_dashboard_renders_without_console_errors(tmp_path):
    playwright = pytest.importorskip("playwright.sync_api",
                                     reason="Playwright is not installed")
    output = tmp_path / "index.html"
    build_dashboard(output)
    errors = []
    with playwright.sync_playwright() as api:
        browser = api.chromium.launch()
        page = browser.new_page()
        page.on("console", lambda message: errors.append(
            f"console {message.type}: {message.text}") if message.type == "error" else None)
        page.on("pageerror", lambda error: errors.append(f"pageerror: {error}"))
        page.goto(output.as_uri(), wait_until="load")
        page.wait_for_function("document.querySelector('#commit').textContent.length > 0")
        assert page.locator("#commit").inner_text()
        assert page.locator("#rows").inner_text() == "413"
        assert page.locator("#tradeSize option").count() > 0
        assert page.locator("#explorerChart").evaluate(
            "canvas => canvas.toDataURL('image/png').length > 1000")
        assert not errors
        browser.close()
