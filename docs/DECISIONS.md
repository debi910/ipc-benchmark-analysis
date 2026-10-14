# Decisions

- Use one bidirectional channel abstraction with independent transport
  directions so every mechanism exercises the same API.
- Use `shm_open` + `ftruncate` + `mmap(MAP_SHARED)`, then call `shm_unlink`
  immediately after mapping. The mapping remains valid while open, without
  leaving persistent `/dev/shm` names.
- Use one shared ring protocol for `shm_spin`, `shm_futex`, and `shm_hybrid`;
  vary only the waiting policy. The hybrid spin window is 2,000 iterations.
- Cap same-core `shm_spin` at 500 iterations and 50 warm-up messages because
  two busy waiters otherwise monopolize one CPU and can starve each handoff.
- Use a 100 ms timeout for each shared futex wait so the runner watchdog flag
  is observed promptly even if no wake arrives.
- Record diagnostic counters in the ring's poll/wait loop: spin loops,
  futex waits, and futex wakes.
- Keep the benchmark on the WSL2 host as the primary result environment; Docker
  support is provided for comparison but is currently untested.
