# IPC-Bench

[![CI](https://github.com/debi910/ipc-benchmark-analysis/actions/workflows/ci.yml/badge.svg)](https://github.com/debi910/ipc-benchmark-analysis/actions/workflows/ci.yml)

This project compares Linux IPC mechanisms using latency, throughput, CPU cost, context switches, and tail latency, then recommends a channel for a workload. The implementation is being delivered in phases from `COPILOT_BRIEF.md`.

Measured on Windows 11 / WSL2 Ubuntu (virtualised). Absolute numbers are not comparable to bare-metal Linux; relative comparisons hold because every mechanism is measured under identical conditions.

## Quick start

```sh
make venv
make check
make bench-quick
./build/ipcbench --list-mechs
```

Quick measurements are written to `results/quick_run.csv`; a full run writes
`results/raw.csv` and refuses to overwrite an existing file unless the
orchestrator is called with `--resume`.

See `docs/DECISIONS.md` for implementation decisions and `PROGRESS.md` for phase status.
