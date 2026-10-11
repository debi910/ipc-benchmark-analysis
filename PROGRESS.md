# Progress

## Phase 0
- Environment: WSL2 Ubuntu 24.04.3, kernel 6.6.87.2-microsoft-standard-WSL2, 8 CPUs, GCC 13.3, Python 3.12.3, Git 2.43.0, Docker unavailable.
- Verification command: `uname -a; lsb_release -a; nproc; gcc --version; python3 --version; git --version; docker --version; pwd`
- Observed: `Linux LAPTOP-IC4U5ITA 6.6.87.2-microsoft-standard-WSL2`, Ubuntu 24.04.3, `8`, GCC 13.3.0, Python 3.12.3, Git 2.43.0, Docker unavailable, `/mnt/d/OS Project`.
- Scaffolded the C++17 build, headers, tests, cleanup policy, and project metadata.
- Needs user: add a GitHub remote URL before pushing.

## Phase 1
- Implemented pipe, FIFO, Unix socket, and POSIX message-queue channels, factory, stats tests, and channel integrity tests.

## Phase 2
- Implemented shared-memory rings with spin/futex-labelled strategies and added shared-memory coverage plus cleanup test.
- Hardened shared memory: real `SYS_futex` calls with shared-memory `FUTEX_WAIT`/`FUTEX_WAKE`, spin-only mode has no futex calls, counters cover spin loops and futex operations, and mappings use `shm_open`/`ftruncate`/`mmap`/immediate `shm_unlink`.
- `make check` uses 200,000 random-size messages x 3 repeats per futex/hybrid mode; channel tests use 16 bytes x 20 and 4096 bytes x 5 per mechanism plus a 1 MiB forced-blocking diagnostic probe; cleanup covers normal teardown and SIGKILL.
- `make check-ci` uses 100,000 messages x 3 repeats; `make stress` uses 1,000,000 messages x 10 repeats.
- Remaining risks: the runner is still an echo smoke-test rather than the full benchmark CLI; Phase 3 replaces it.
