#!/usr/bin/env python3
"""Run the IPC matrix sequentially so mounted-drive locking is not required."""
from __future__ import annotations

import argparse
import json
import os
import random
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MECHANISMS = ["pipe", "fifo", "mq", "uds", "shm_spin", "shm_futex", "shm_hybrid"]
SIZES = [16, 256, 4096, 65536, 1048576]


def output(command: list[str]) -> str:
    return subprocess.run(command, cwd=ROOT, check=False, text=True,
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT).stdout.strip()


def system_info() -> dict:
    version = Path("/proc/version").read_text(errors="replace")
    info = {
        "kernel": output(["uname", "-srvm"]),
        "distro": output(["bash", "-lc", "lsb_release -ds"]),
        "cpu_model": next((line.split(":", 1)[1].strip() for line in Path("/proc/cpuinfo").read_text().splitlines()
                           if line.startswith("model name")), "unknown"),
        "cores": os.cpu_count(),
        "env": "wsl2" if "microsoft" in version.lower() else "linux",
        "compiler": output(["g++", "--version"]).splitlines()[0],
        "git_commit": output(["git", "rev-parse", "HEAD"]),
    }
    governor = Path("/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor")
    info["cpu_governor"] = governor.read_text().strip() if governor.exists() else "unreadable"
    return info


def main() -> int:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--quick", action="store_true")
    group.add_argument("--full", action="store_true")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--only-mech", choices=MECHANISMS)
    parser.add_argument("--timeout", type=int, default=60)
    args = parser.parse_args()
    quick = args.quick or not args.full
    sizes = [16, 4096, 65536] if quick else SIZES
    reps = 1 if quick else 5
    fraction = 0.2 if quick else 1.0
    results = ROOT / "results"
    (results / "logs").mkdir(parents=True, exist_ok=True)
    (results / "figures").mkdir(parents=True, exist_ok=True)
    results.joinpath("system_info.json").write_text(json.dumps(system_info(), indent=2) + "\n")
    csv = results / "raw.csv"
    existing = csv.read_text(errors="replace") if args.resume and csv.exists() else ""
    jobs = [(m, mode, size, rep) for m in MECHANISMS if not args.only_mech or m == args.only_mech
            for mode in ("pingpong", "stream") for size in sizes for rep in range(reps)]
    random.Random(20261012).shuffle(jobs)
    print("WSL2/virtualised run: close heavy applications and keep the laptop plugged in.")
    for run_id, (mech, mode, size, rep) in enumerate(jobs, 1):
        marker = f",{mech},{mode},{size},"
        if args.resume and marker in existing:
            continue
        subprocess.run(["bash", str(ROOT / "scripts" / "cleanup.sh")], cwd=ROOT, check=True)
        default = (20000 if size <= 65536 else 2000) if mode == "pingpong" else max(2000, min(200000, 268435456 // size))
        iters = max(1, int(default * fraction))
        warmup = iters // 10 if mode == "pingpong" else 0
        command = [str(ROOT / "build" / "ipcbench"), "--mech", mech, "--mode", mode,
                   "--size", str(size), "--iters", str(iters), "--warmup", str(warmup),
                   "--pin", "cross", "--run-id", str(run_id), "--csv", str(csv),
                   "--timeout", str(args.timeout)]
        started = time.monotonic()
        completed = subprocess.run(command, cwd=ROOT, text=True, stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT)
        log = results / "logs" / f"run_{run_id:04d}.log"
        log.write_text(f"$ {' '.join(command)}\n{completed.stdout}\n")
        print(f"[{run_id}/{len(jobs)}] {mech:10s} {mode:8s} {size:7d}B rep={rep + 1} "
              f"rc={completed.returncode} {time.monotonic() - started:.2f}s", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
