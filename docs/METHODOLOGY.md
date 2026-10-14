# Methodology

The primary matrix has seven mechanisms, two modes, five sizes
(16, 256, 4096, 65536, and 1048576 bytes), cross-core pinning, and five
repetitions: 350 rows. The secondary matrix has ping-pong only, sizes 16, 4096,
and 65536 bytes, same-core pinning, and three repetitions: 63 rows.

Ping-pong records round-trip-time percentiles after warm-up; it is an RTT
measurement, not one-way latency. Stream records message throughput. Each
message contains a sequence/checksum pattern; the receiver checks the full
payload at the boundaries and cheap sequence/prefix/suffix invariants in the
loop. A mismatch aborts the run.

Runs use randomized order with a fixed seed, cleanup before every invocation,
and a 60-second watchdog. CPU pinning separates cross-core and same-core
effects. `getrusage` supplies user/system CPU and context-switch counts.
Repetitions are aggregated by median, while min/max and tail percentiles expose
variability. The shared-memory ring is intentionally small enough to force
blocking in tests, and message queues are allowed to exercise chunking.

The same-core `shm_spin` benchmark is capped at 500 iterations and 50 warm-up
iterations to prevent two busy waiters on one CPU from starving the scheduler.
The completed CSV shows that `shm_spin` same-core rows use 500 iterations,
whereas `shm_hybrid` and the other same-core mechanisms use the default 20,000
iterations and 2,000 warm-up. Analyses must therefore compare same-core values
with this iteration-count difference visible, not treat them as identical loads.

Threats to validity include WSL2 virtualization and background activity,
unreadable CPU-governor state, frequency scaling, hyperthread placement, one
physical machine, `getrusage` granularity, message-queue fragmentation and
limits, and the fact that five repetitions cannot characterize every scheduler
tail.
