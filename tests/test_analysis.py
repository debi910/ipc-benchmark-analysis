import subprocess
import sys
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parent.parent
CSV = ROOT / "tests" / "synthetic.csv"


def make_csv(path):
    rows = []
    for mech, p50, mb in [("pipe", 100, 10), ("shm_futex", 50, 8), ("uds", 200, 12)]:
        rows.append({"timestamp": 1, "git_commit": "-", "mech": mech, "mode": "pingpong",
                     "size_bytes": 4096, "iters": 10, "warmup": 1, "pin": "cross", "run_id": 1,
                     "chunked": False, "status": "ok", "mean_ns": p50, "p50_ns": p50,
                     "p90_ns": p50, "p99_ns": p50 * 2, "p999_ns": p50 * 2, "min_ns": p50,
                     "max_ns": p50 * 2, "stddev_ns": 1, "msgs_per_s": 1, "mb_per_s": mb,
                     "wall_s": 1, "cpu_user_s": p50 / 1000, "cpu_sys_s": 0, "cpu_pct": 1,
                     "vol_ctx": 1, "invol_ctx": 0, "ctx_per_msg": 0.1})
    pd.DataFrame(rows).to_csv(path, index=False)


def test_report_and_recommend(tmp_path):
    csv_path = tmp_path / "synthetic.csv"
    make_csv(csv_path)
    report_dir = tmp_path / "report_out"
    subprocess.run([sys.executable, "analysis/make_report.py", "--input", str(csv_path),
                    "--output", str(report_dir)], cwd=ROOT, check=True)
    result = subprocess.run([sys.executable, "analysis/recommend.py", "--input", str(csv_path),
                             "--size", "4096", "--pattern", "pingpong",
                             "--goal", "min_latency", "--top", "1"],
                            cwd=ROOT, check=True, capture_output=True, text=True)
    assert "shm_futex" in result.stdout
