# Results

## Dataset

The completed `results/raw.csv` contains 413 data rows, all with
`status=ok`: 350 cross-core primary rows and 63 same-core secondary rows.
The machine metadata is in `results/system_info.json`: WSL2 Ubuntu 24.04.3,
Linux 6.6.87.2, 8 vCPUs, Intel i5-1135G7, GCC 13.3, and an unreadable CPU
governor. Absolute values should not be generalized beyond this environment.

## Automatically generated measurements

The tables and crossover analysis in `results/summary.md`, the recommender
table in `results/recommendation_table.md`, and the seven figures in
`results/figures/` are generated from `results/raw.csv`.

## Recommender examples

Cross-core ping-pong at 4096 bytes, goal `min_cpu`:

```text
mech       size_bytes  cpu_user_s
mq         4096        0.040131
pipe       4096        0.061885
uds        4096        0.065497
```

Cross-core ping-pong at 65536 bytes, goal `balanced`:

```text
mech       size_bytes  p50_ns
shm_spin   65536       15065.5
mq         65536       62726.0
pipe       65536       67471.0
```

The balanced score uses p99, CPU/msg, and context switches; the displayed p50
is a readable ranking column, not the complete score.

## Anomalies

- `scripts/sanity_check_results.py` reports two throughput/wall consistency
  warnings, at rows 121 and 185 (FIFO and pipe, 256-byte stream). The stored
  throughput differs from `iters / wall_s` by more than one message, so these
  rows should be treated as instrumentation/accounting anomalies rather than
  discarded benchmark failures.
- It reports duplicate mechanism/mode/size combinations because repetitions are
  intentionally represented as separate rows. There are no missing combinations
  and all 413 statuses are `ok`.
- WSL2 virtualization is reported as an expected warning.
- At 16-byte cross-core ping-pong, `shm_hybrid` has the lowest median p50 RTT
  (311 ns), followed by `shm_spin` (367 ns). Thus `shm_spin` is not the
  fastest at this size; the hybrid's short polling/futex policy is a measured
  result, not proof of a universal cause.
- Cross-core p50 repetition CV exceeds 20% for `shm_spin` at 4096 bytes
  (40.9%), `shm_spin` at 65536 bytes (35.3%), `shm_hybrid` at 16 bytes
  (27.4%), and UDS at 4096 bytes (25.8%). This supports a variability
  hypothesis involving scheduling and synchronization, but does not establish
  causation.
- Tail gaps are substantial. Median cross-core p99/p50 ratios are about 2.66
  for UDS, 2.10 for MQ, 2.09 for FIFO, 2.08 for `shm_futex`, 2.03 for pipe,
  1.56 for `shm_hybrid`, and 1.55 for `shm_spin`. The largest observed ratio
  is 4.76 for `shm_spin`. These are measured tail amplifications, not proof
  of a particular kernel mechanism.
- Same-core `shm_spin` rows use the safety cap of 500 iterations and 50
  warm-up messages. Same-core `shm_hybrid` rows use the default 20,000
  iterations and 2,000 warm-up, as do the other same-core mechanisms. Any
  comparison across those rows must account for the unequal workload.

## Interpretation

The data supports the hypothesis that shared-memory synchronization can reduce
small-message cross-core latency and increase stream throughput on this host.
It also supports a trade-off hypothesis: spin-based methods can reduce
context-switch activity while consuming CPU, and their tails/variance can be
more sensitive to scheduling. These statements are hypotheses supported by the
observed measurements, not proven causal explanations.

## Reproducibility

Run `python3 scripts/sanity_check_results.py results/raw.csv`, then
`make report`. The full benchmark must not be rerun merely to regenerate these
artifacts.
