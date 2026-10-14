# Presentation outline

1. **Question and gap** — Why compare latency, throughput, CPU, context
   switches, and tail behavior together?
2. **Mechanisms** — Pipe, FIFO, POSIX MQ, UDS, and three shared-memory
   synchronization policies.
3. **Experimental design** — 413 rows, two modes, sizes, repetitions,
   pinning, warm-up, integrity checks, and watchdog.
4. **System caveat** — Windows 11 / WSL2, eight vCPUs, unreadable governor.
5. **Headline figure** — Latency–CPU trade-off from
   `results/figures/latency_vs_cpu_tradeoff.png`.
6. **Latency result** — Shared-memory variants lead at small and medium
   cross-core ping-pong sizes; tail ratios remain mechanism- and size-dependent.
7. **Throughput result** — Shared memory leads the measured stream cases,
   especially at large messages.
8. **Same-core result** — Spin is capped and its reduced iteration count is
   explicitly reported; hybrid retains the default workload.
9. **Recommendations** — Show the two measured recommender examples and
   emphasize that they are machine-specific heuristics.
10. **Limitations and future work** — Bare-metal replication, more hosts,
    more repetitions, and power measurements.
