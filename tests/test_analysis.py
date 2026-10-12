import subprocess
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
CSV_COLUMNS = [
    "timestamp", "git_commit", "mech", "mode", "size_bytes", "iters", "warmup",
    "pin", "run_id", "chunked", "status", "mean_ns", "p50_ns", "p90_ns",
    "p99_ns", "p999_ns", "min_ns", "max_ns", "stddev_ns", "msgs_per_s",
    "mb_per_s", "wall_s", "cpu_user_s", "cpu_sys_s", "cpu_pct", "vol_ctx",
    "invol_ctx", "ctx_per_msg",
]


def make_csv(path, sizes=(1024, 4096)):
    rows = []
    values = {
        "pipe": (100, 150, 1, 1, 10),
        "uds": (200, 300, 3, 3, 30),
        "shm_futex": (50, 100, 2, 2, 20),
    }
    for size in sizes:
        for mech, (p50, p99, cpu, ctx, mb) in values.items():
            scale = size / 1024
            rows.append(dict(zip(CSV_COLUMNS, [
                1, "-", f" {mech} ", " pingpong ", size, 10, 1, " cross ",
                1, False, " ok ", p50 * scale, p50 * scale, p50 * scale,
                p99 * scale, p99 * scale, p50 * scale, p99 * scale, 1, 1,
                mb * scale, 1, cpu * scale, 0, 1, ctx, 0, ctx / 10,
            ])))
    pd.DataFrame(rows).to_csv(path, index=False)


def run_recommend(path, goal, extra=()):
    return subprocess.run(
        [sys.executable, "analysis/recommend.py", "--input", str(path),
         "--size", "2048", "--pattern", "pingpong", "--goal", goal,
         "--top", "1", *extra],
        cwd=ROOT, check=True, capture_output=True, text=True,
    )


def test_report_and_whitespace_robust_loading(tmp_path):
    csv_path = tmp_path / "synthetic.csv"
    make_csv(csv_path)
    report_dir = tmp_path / "report_out"
    subprocess.run([sys.executable, "analysis/make_report.py", "--input", str(csv_path),
                    "--output", str(report_dir)], cwd=ROOT, check=True)
    result = run_recommend(csv_path, "min_latency")
    assert "shm_futex" in result.stdout


def test_recommender_winner_for_each_goal(tmp_path):
    csv_path = tmp_path / "goals.csv"
    make_csv(csv_path)
    assert "shm_futex" in run_recommend(csv_path, "min_latency").stdout
    assert "uds" in run_recommend(csv_path, "max_throughput").stdout
    assert "pipe" in run_recommend(csv_path, "min_cpu").stdout
    assert "pipe" in run_recommend(csv_path, "balanced").stdout


def test_log_interpolation_and_clamping_warning(tmp_path):
    csv_path = tmp_path / "interpolation.csv"
    make_csv(csv_path, sizes=(1024, 4096))
    result = run_recommend(csv_path, "min_latency")
    assert "2048" in result.stdout
    clamped = subprocess.run(
        [sys.executable, "analysis/recommend.py", "--input", str(csv_path),
         "--size", "64", "--pattern", "pingpong", "--goal", "min_latency"],
        cwd=ROOT, check=True, capture_output=True, text=True,
    )
    assert "clamping" in clamped.stderr


def test_p99_filter(tmp_path):
    csv_path = tmp_path / "filter.csv"
    make_csv(csv_path)
    result = run_recommend(csv_path, "max_throughput", ("--max-p99-us", "0.5"))
    assert "uds" not in result.stdout
