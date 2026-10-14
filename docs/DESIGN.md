# Design

## Architecture

The executable has a small `Channel` abstraction with `setup`, `attach`, `send`,
`recv`, `chunked`, and `teardown` operations. The runner creates two independent
directions, forks a child, optionally pins each process, exchanges messages, and
records timing and resource statistics in one CSV row.

```text
parent process                         child process
      |                                      |
      | send A ----------------------------> |
      | <--------------------------- send B  |
      |                                      |
      +----------- control socket -----------+
             status and rusage report
```

Pipe, FIFO, message queue, and UDS use kernel-managed transport. Shared-memory
channels use two rings so each process owns one producer direction.

## Shared-memory ring and futex protocol

Each ring contains atomic head/tail positions, a payload region, and diagnostic
counters. Creation uses `shm_open`, `ftruncate`, `mmap(MAP_SHARED)`, then
immediately `shm_unlink`s the name. The mapping remains alive until both
processes close it.

The producer reserves space by observing `head - tail`; the consumer observes
`head - tail` for available data. A waiter loads the relevant atomic value and
calls `SYS_futex` with `FUTEX_WAIT` (without `FUTEX_PRIVATE_FLAG`). The producer
updates the atomic value before `FUTEX_WAKE`. If a wake occurs before the wait,
the value mismatch causes the futex call to return immediately; this is the
key lost-wake avoidance rule. The loop always rechecks the ring predicate after
returning.

More specifically, the consumer reads the futex word, sets
`consumer_waiting`, re-checks `head`, and only then calls `futex_wait`. The
producer publishes `head`, bumps the futex word, and reads the waiting flag
before deciding whether to wake. A producer wake racing with the consumer's
registration is safe because the kernel compares the futex word with the
consumer's previously read value: a changed value makes `FUTEX_WAIT` return
immediately. The flag covers the notification decision, so the read/check/wait
sequence cannot lose a wakeup.

`shm_spin` only polls and calls no futex. `shm_futex` waits directly. `shm_hybrid`
polls for the configured spin window and then falls back to the same shared
futex protocol. The tests assert these distinctions with diagnostic counters.

## Cleanup and failure handling

Names are unlinked immediately where possible. Normal teardown and SIGKILL
cleanup tests inspect `/dev/shm`, FIFO paths, and `/dev/mqueue`. The runner has
a 60-second supervisor watchdog; on timeout it kills the child, interrupts the
parent, writes a `timeout` row, and tears down the mapping.

The shared-memory stress test passed 10 repeats of 1,000,000 messages for both
`shm_futex` and `shm_hybrid`, supporting the implementation's wakeup and
wrap-around behavior under sustained load.
