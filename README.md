# IPC Benchmark Analysis

[![CI](https://github.com/debi910/ipc-benchmark-analysis/actions/workflows/ci.yml/badge.svg)](https://github.com/debi910/ipc-benchmark-analysis/actions/workflows/ci.yml)

This project measures seven Linux IPC mechanisms—pipe, FIFO, POSIX message queue,
Unix-domain socket, and three shared-memory rings—using latency, throughput,
CPU time, context switches, and tail latency. The research gap is a reproducible
comparison that combines these metrics, tests both ping-pong and streaming, and
turns measured trade-offs into workload recommendations. The implementation is
written from scratch; it is not copied from the reference repositories listed in
`docs/RELATED_WORK.md`.

## Results at a glance

The completed run contains 413 successful rows: 350 cross-core primary rows and
63 same-core secondary rows. At 16-byte cross-core ping-pong, median p50 RTT was
311 ns for `shm_hybrid`, 367 ns for `shm_spin`, and 43,844 ns for pipe. At
1 MiB cross-core streaming, median throughput was 2,212.17 MB/s for `shm_spin`,
1,616.25 MB/s for `shm_hybrid`, and 619.33 MB/s for pipe. These are observations
from one machine, not universal performance claims.

## WSL2 disclaimer

Measurements were collected on Windows 11 using WSL2 Ubuntu 24.04.3, Linux
6.6.87.2, an 8-vCPU Intel i5-1135G7 system, and GCC 13.3. The CPU governor was
unreadable. WSL2 virtualization, scheduling, frequency scaling, and background
Windows activity can affect absolute values and tail latency. Use the results
primarily as within-run comparisons.

## Quick start

Run these commands from WSL:

```sh
cd "/mnt/d/OS Project"
make venv
make check
make bench-quick
make report
python3 analysis/recommend.py --size 4096 --pattern pingpong --goal min_cpu
```

`make bench-full` creates a fresh `results/raw.csv`, runs the 350-row cross-core
matrix, then appends the 63-row same-core matrix. It refuses to overwrite an
existing full CSV unless the underlying script is invoked with `--resume`.
To add only the secondary matrix to an existing primary run, use
`make bench-secondary`.

## Docker

```sh
make docker-build
make docker-quick
```

The Docker image provides the compiler and Python analysis environment. IPC
results from a container are not directly comparable with the WSL2 run.

## Repository layout

- `src/`, `include/`: benchmark implementation and channel interface.
- `tests/`: C++ channel/stress/cleanup tests and analysis tests.
- `scripts/`: experiment orchestration, sanity checks, and review bundle creation.
- `analysis/`: report and recommendation programs.
- `results/`: raw CSV, system metadata, summaries, figures, and logs.
- `docs/`: design, methodology, related work, and measured results.

## Reading the results

Start with `results/summary.md`, then inspect the seven PNG figures in
`results/figures/`. `p50_ns` and `p99_ns` are ping-pong RTT percentiles;
`mb_per_s` is stream throughput; CPU/msg is derived from user and system CPU
time divided by the recorded iteration count. Recommendations are measured-data
heuristics and include a machine-specific disclaimer.

## What is novel vs the reference repositories?

The reference projects generally provide a narrower latency or throughput
comparison. This project adds a common bidirectional interface, full-payload
integrity checks, warm-up and randomized repetitions, same-core versus cross-core
pinning, p50/p99/tail analysis, CPU and context-switch accounting, real futex
protocol diagnostics, cleanup-after-kill tests, a watchdog, and a recommender
that exposes the latency/throughput/CPU trade-off. The novelty claim is about
the combination and reproducible workflow, not a claim that any individual IPC
primitive is new.

## Limitations and licence

The study uses one WSL2 host, five primary sizes, three same-core sizes, and
five primary repetitions. `getrusage` and virtualization make CPU and scheduling
metrics noisy. Message-queue limits, ring capacity, pinning, and scheduler
state can change the ranking. See `docs/METHODOLOGY.md` and
`docs/RESULTS.md`.

Code is released under the repository licence. External projects and the paper
listed in `docs/RELATED_WORK.md` remain the property of their respective
authors.
