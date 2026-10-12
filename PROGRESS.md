# Progress

## Phase 0
- Environment: WSL2 Ubuntu 24.04.3, kernel 6.6.87.2-microsoft-standard-WSL2, 8 CPUs, GCC 13.3, Python 3.12.3, Git 2.43.0, Docker unavailable.
- Verification command: `uname -a; lsb_release -a; nproc; gcc --version; python3 --version; git --version; docker --version; pwd`
- Observed: `Linux LAPTOP-IC4U5ITA 6.6.87.2-microsoft-standard-WSL2`, Ubuntu 24.04.3, `8`, GCC 13.3.0, Python 3.12.3, Git 2.43.0, Docker unavailable, `/mnt/d/OS Project`.
- Scaffolded the C++17 build, headers, tests, cleanup policy, and project metadata.
- Git remote configured as `origin`; pushes completed after Phases 2, 3, and 4.

## Phase 1
- Implemented pipe, FIFO, Unix socket, and POSIX message-queue channels, factory, stats tests, and channel integrity tests.

## Phase 2
- Implemented shared-memory rings with spin/futex-labelled strategies and added shared-memory coverage plus cleanup test.
- Hardened shared memory: real `SYS_futex` calls with shared-memory `FUTEX_WAIT`/`FUTEX_WAKE`, spin-only mode has no futex calls, counters cover spin loops and futex operations, and mappings use `shm_open`/`ftruncate`/`mmap`/immediate `shm_unlink`.
- `make check` uses 200,000 random-size messages x 3 repeats per futex/hybrid mode; channel tests use 16 bytes x 20 and 4096 bytes x 5 per mechanism plus a 1 MiB forced-blocking diagnostic probe; cleanup covers normal teardown and SIGKILL.
- `make check-ci` uses 100,000 messages x 2 repeats; `make stress` uses 1,000,000 messages x 10 repeats.
- Full `make stress` result: all 10 futex repeats and all 10 hybrid repeats passed.
- Remaining risks: the runner is still an echo smoke-test rather than the full benchmark CLI; Phase 3 replaces it.

## Phase 3
- Added ping-pong and stream process benchmarks, warm-up, RTT samples, rusage/context-switch metrics, watchdog timeout, CPU pinning, integrity checks, and append-only CSV output.
- Manual smoke coverage passed for all seven mechanisms: ping-pong at 16 bytes x 3 iterations and stream at 65,536 bytes x 3 iterations, cross-pinned.

## Phase 4
- Added quoted-path cleanup and experiment orchestration with quick/full/resume/filter/timeout options and WSL2 `system_info.json` capture.
- Quick matrix: 7 mechanisms x 2 modes x 3 sizes (16, 4096, 65536) x 1 repetition; each ping-pong run uses 20% of its default iterations and stream uses 20% of its default N.

## Phase 5 preparation
- Moved the 42-run quick matrix to `results/quick_run.csv`; the two excluded rows were the earlier manual `shm_hybrid` smoke runs (16-byte ping-pong and 4096-byte stream), not additional matrix jobs.
- `bench-full` now targets a fresh `results/raw.csv` and refuses an existing file unless the orchestrator is explicitly invoked with `--resume`.
- Expanded channel coverage to sizes 16, 17, 1000, 4096, 65536 (1000 echoes each) and 1048576 (100 echoes), plus a 4 KiB ring with 65536-byte messages x 20 for each shared-memory mode.
- Added CI configuration, sanity checking, report generation, recommender, and synthetic-data pytest coverage. Full benchmark intentionally not run.

## Pre-Phase 5 hygiene
- CSV rows now contain trimmed fields and real short Git hashes, with `-dirty` appended when the checkout has uncommitted changes.
- Regenerated `results/quick_run.csv`, summaries, and figures after the hygiene fix; the sanity checker reports only the expected WSL virtualization warning.
- The full matrix is estimated at 413 rows: 350 primary runs plus 63 same-core secondary runs. Full execution remains intentionally deferred.
