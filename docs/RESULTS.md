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

Cross-core ping-pong at 4096 bytes, goal `min_cpu` (all seven ranked rows):

```text
      mech  size_bytes  p50_ns   p99_ns  cpu_ns_per_msg  ctx_per_msg    score
shm_hybrid        4096  1482.0  2129.08         5991.90      0.00010  5991.90
  shm_spin        4096  1491.0  2168.05         6273.65      0.00000  6273.65
      pipe        4096 36756.0 78435.60        38380.75      2.19355 38380.75
 shm_futex        4096 39252.0 78833.00        39236.15      2.19125 39236.15
        mq        4096 41596.0 80566.10        41062.10      2.19255 41062.10
        uds        4096 34549.0 86672.00        41463.40      2.72450 41463.40
      fifo        4096 42128.5 90878.60        43293.50      2.19360 43293.50
```

Cross-core ping-pong at 65536 bytes, goal `balanced` (all seven ranked rows):

```text
      mech  size_bytes  p50_ns   p99_ns  cpu_ns_per_msg  ctx_per_msg    score
  shm_spin       65536 12974.0  22321.3        67694.00      0.00000  0.000000
shm_hybrid       65536 13701.0  28824.6        77567.30      0.00050  0.079241
 shm_futex       65536 54429.0 114572.0        80514.30      2.19445  0.415219
      pipe       65536 71027.5 136734.0        97130.45      2.19690  0.577161
      fifo       65536 72784.0 142303.0        98542.95      2.19725  0.600300
        mq       65536 76313.0 166826.0       128263.95      2.22800  0.852732
        uds       65536 86154.5 179698.0       130692.20      4.41775  1.000000
```

The balanced score uses min-max-normalised p99, CPU/msg, and context switches
with weights 0.4, 0.4, and 0.2. The output prints every component and score
so rankings are auditable. Recommendations use the existing measured CSV and
are not benchmark reruns.

The generated summary reports every quoted latency and CPU median with its
five-repetition min-max range. For example, at 16 bytes `shm_hybrid` is
311 ns [163-379] and `shm_spin` is 367 ns [338-399]; at 1 MiB stream,
`shm_spin` is 2212.17 MB/s [1755.43-2281.31], `shm_hybrid` is 1616.25 MB/s
[1386.64-1837.06], and pipe is 619.33 MB/s [554.78-630.23].

## Same-core results

Same-core ping-pong suggests three distinct regimes: pipe/MQ/UDS are roughly
3-8 us RTT, `shm_hybrid` is roughly 190 us RTT, and `shm_spin` is roughly
8 ms RTT. These are hypotheses supported by the medians, not proven causes.
The `shm_spin` rows use 500 iterations and 50 warm-up messages; the other
same-core mechanisms, including `shm_hybrid`, use 20,000 iterations and 2,000
warm-up messages. Spin CPU cost at low message rates is not measured here:
the workload is back-to-back. The spin window is an iteration count whose
duration depends on the CPU, and all results are WSL2/virtualized.

## Anomalies

- The sanity checker permits a 0.001% throughput/wall tolerance. Rows 121 and
  185 (FIFO and pipe, 256-byte stream) agree within that tolerance and are not
  anomalies.
- It reports duplicate mechanism/mode/size combinations because repetitions are
  intentionally represented as separate rows. There are no missing combinations
  and all 413 statuses are `ok`.
- WSL2 virtualization is reported as an expected warning.
- At 16-byte cross-core ping-pong, `shm_hybrid` has median p50 RTT 311 ns
  (min-max 163-379 ns), while `shm_spin` has 367 ns (338-399 ns). With five
  repetitions and overlapping min-max ranges, they are statistically
  indistinguishable; the data does not support claiming that hybrid beats spin.
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
- All quoted medians should be read with their measured min-max ranges in
  `results/summary.md`; same-core `shm_spin` rows use 500 iterations and 50
  warm-up, while `shm_hybrid` and the other same-core mechanisms use the
  default 20,000 and 2,000.

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
