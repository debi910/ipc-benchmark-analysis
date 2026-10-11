# IPC-Bench: Copilot Execution Brief

> Save this file in the repo root as `COPILOT_BRIEF.md` (on the D: drive, which is `/mnt/d/<folder>` inside WSL). Then tell Copilot (agent mode):
> "Read COPILOT_BRIEF.md fully, especially section 2A. Execute Phases 0-2 (section 12), run `make check`, commit and push, update PROGRESS.md, then stop and report."
> Repeat with the next phases.

---

## 0. Rules of engagement (read first)

1. You are building this project end to end: code, tests, experiments tooling, analysis, docs.
2. Work in the phases in section 12. After each phase: run `make check`, fix failures, `git commit`, append a short entry to `PROGRESS.md`.
3. Do not ask questions unless truly blocked. Make a reasonable decision and log it in `docs/DECISIONS.md` (one line: decision + why).
4. Keep files small and modular (aim for under 250 lines each), well commented, no dead code.
5. Never print huge outputs in the terminal (use `head`, `tail`, `| wc -l`). Keep logs in `results/logs/`.
6. You have a terminal: build and run tests yourself, inside WSL (section 2A). If a command needs `sudo`, a password, or an interactive login, do NOT try to type it; write the exact command in `PROGRESS.md` under "Needs user" and continue with other work.
7. Do not invent citations, benchmark numbers or results. Every number in docs must come from `results/`. Placeholders must say `TODO(results)`.
8. Do not require root. Do not modify sysctls. Do not add dependencies beyond those in section 2.
9. Git: commit at the end of every phase with a conventional message (`feat:`, `test:`, `docs:`, `fix:`) and push if a remote is configured (section 2A). Never commit secrets, `.venv/`, or build output.

---

## 1. Project

**Title:** *Beyond Speed: A Latency-and-CPU-Cost Study of Linux IPC with a Workload-Aware Recommender*

**Context.** This is a university Operating Systems project (Linux). The core idea of benchmarking IPC mechanisms already exists in public repos, so this project must contribute something beyond raw speed tables.

**Research gap (what existing work lacks).**
- Typical IPC benchmarks (e.g. goldsborough/ipc-bench, rigtorp/ipc-bench) report ping-pong latency or messages per second only. They do not report CPU cost, context switches, or tail latency, and some admit missing warm-up and old, sub-optimal configurations.
- Published results disagree on where shared memory overtakes pipes/sockets (roughly 64 KB in some sources, 8 MB in another), so the crossover depends on method and machine.
- Shared-memory IPC has a latency vs CPU tradeoff (busy-spinning is fast but burns CPU; futex blocking saves CPU but adds wake-up latency). Few simple benchmarks quantify it.
- Benchmark methodology is error-prone (e.g. a public eventfd benchmark was criticised for sharing one eventfd between both directions and measuring blocking/scheduler latency).
- No simple tool found that turns measurements into a recommendation ("which IPC for my workload?").

**Objectives.**
- O1. Implement five Linux IPC mechanisms behind one interface: pipe, FIFO (named pipe), POSIX message queue, Unix domain socket, shared memory.
- O2. Implement three waiting strategies for shared memory (spin, futex, hybrid spin-then-futex), giving 7 channels in total.
- O3. Measure per mechanism and message size: latency distribution (mean, p50, p90, p99, p99.9, max), throughput (msgs/s, MB/s), CPU time per message, context switches per message.
- O4. Run controlled experiments with proper methodology (warm-up, repetitions, CPU pinning, timeouts, integrity checks).
- O5. Visualise the results and identify crossover points and the latency-vs-CPU tradeoff.
- O6. Provide a recommender CLI that, given a workload (message size, pattern, goal), recommends a mechanism with reasoning from the measured data.

**Contributions to emphasise in docs:** C1 cost-aware metrics (CPU, context switches, tail latency); C2 shared-memory sync strategy comparison; C3 workload-aware recommender; C4 methodological rigour (warm-up, pinning, repetitions, integrity verification, reproducibility).

---

## 2. Tech constraints

- Linux (Ubuntu 22.04+), x86-64 or ARM64. Must degrade gracefully (use a portable `cpu_relax()` fallback).
- C++17, `g++ -O2 -Wall -Wextra -pthread`, link `-lrt`. Single `Makefile`, no CMake.
- No third-party C++ libraries (no GoogleTest, no Boost). Tests are self-contained `assert`-style binaries with a tiny helper header.
- Python 3.9+ with only `pandas`, `matplotlib`, `numpy`, `pytest`. Provide `requirements.txt`. Always use a virtualenv on the Linux filesystem at `$(VENV)`, default `$HOME/.venvs/ipc-bench` (Ubuntu 24.04 blocks system-wide `pip install`, and venvs work poorly on Windows-mounted drives); `make venv` creates it, and all scripts/Makefile targets call `$(VENV)/bin/python`.
- Timing: `clock_gettime(CLOCK_MONOTONIC)`. CPU cost: `getrusage`. Pinning: `sched_setaffinity`.

---

## 2A. Environment: Windows 11 + WSL2 Ubuntu + Docker Desktop + GitHub

- **Where to work.** The host is a Windows 11 laptop. The project folder is on the Windows **D: drive** (`D:\<folder>`, which is `/mnt/d/<folder>` inside WSL) and the source of truth stays there. You (the Copilot app) edit files on D:, but **every build, test, benchmark and git command must run inside WSL2 Ubuntu**, never in PowerShell/cmd. If your terminal is PowerShell, wrap commands like this: `wsl -e bash -lc "cd /mnt/d/<folder> && <command>"` (or open a WSL terminal first and `cd /mnt/d/<folder>`). At the very start, verify and paste into `PROGRESS.md`: `uname -a; lsb_release -a; nproc; gcc --version; python3 --version; git --version; docker --version; pwd`.
- **Rules because the project lives on a Windows-mounted drive** (it is slower and lacks some Linux semantics):
  1. The Python venv lives on the Linux filesystem: `$HOME/.venvs/ipc-bench` (never inside the project folder).
  2. FIFOs, sockets and any other temp files used by the benchmark go in `/tmp` only. The code must refuse (with a clear error) any path under `/mnt/`. Shared memory uses `/dev/shm` and message queues use the kernel namespace, so none of the measured IPC touches the D: drive.
  3. `flock` may be unreliable on this mount, so locking is best-effort (see section 6).
  4. Add an `.editorconfig` (`root = true`, `end_of_line = lf`, `insert_final_newline = true`, UTF-8) so Windows editors write LF. If CR characters are found, fix them with `sed -i 's/\r$//' <file>`.
  5. Use only the WSL `git` in this repo (not Windows git) to avoid line-ending and file-mode churn; run `git config core.fileMode false`. If git reports "dubious ownership", run `git config --global --add safe.directory "$PWD"`.
  6. Builds are small, so `build/` may stay in the project folder; do not run the full benchmark while heavy Windows tasks (indexing, syncing, antivirus scans) are running.
- **One-time prerequisites (the user installs these; do not try `sudo` yourself):** `sudo apt update && sudo apt install -y build-essential git python3-venv python3-pip`. If anything is missing, write the exact command under "Needs user" in `PROGRESS.md`.
- **WSL2 is a lightweight VM.** Expect more jitter than bare-metal Linux, an unreadable CPU governor, `/dev/mqueue` probably not mounted, and possibly few vCPUs. Handle all of this gracefully:
  - Detect WSL via `/proc/version` containing "microsoft"; record `env: wsl2` in `system_info.json`.
  - Need at least 2 vCPUs for `cross` pinning (`nproc`). If only 1, write to `PROGRESS.md`: set `processors=4` in `%UserProfile%\.wslconfig` and run `wsl --shutdown` from Windows.
  - If a mechanism is unsupported (e.g. `mq_open` fails with `ENOSYS`), skip it with a clear message and record `status=unsupported`; do not fail the whole suite. Tests for that mechanism print `SKIPPED` with the reason.
  - Every README, doc and figure caption must state: "Measured on Windows 11 / WSL2 Ubuntu (virtualised). Absolute numbers are not comparable to bare-metal Linux; relative comparisons hold because every mechanism is measured under identical conditions." This is a stated limitation, not a defect.
- **Line endings.** Create all files with LF endings. Add `.gitattributes` (`* text=auto eol=lf` and `*.sh text eol=lf`). `make check` must fail if any `.sh` file or the `Makefile` contains carriage-return characters.
- **Docker Desktop (WSL2 backend) is available but optional.** Use it for (a) a reproducible `Dockerfile` (`ubuntu:24.04` + build-essential + python3-venv) so anyone can `docker build` and run the quick benchmark, and (b) the optional Phase 8 container comparison. Containers on Docker Desktop share the WSL2 VM kernel; say so in the docs. Core results must not depend on Docker.
- **GitHub.** The user creates an empty GitHub repo and provides its URL. Then `git remote add origin <url>`, branch `main`, push after every phase (if auth fails, put the command under "Needs user"). Add `LICENSE` (MIT). `.gitignore`: `build/`, `.venv/`, `__pycache__/`, `results/logs/`, `*.tar.gz`. **Do commit** `results/raw.csv`, `results/system_info.json`, `results/summary.md` and `results/figures/` as evidence. Add `.github/workflows/ci.yml`: on push/PR, `ubuntu-latest`, run `make venv` and `make check-ci` (build + all tests with the stress test shortened to 100k messages x 2 repeats, pip cache enabled). The README shows the CI badge.

---

## 3. Repository layout (create exactly this)

```
ipc-bench/
├── COPILOT_BRIEF.md
├── README.md
├── PROGRESS.md
├── Makefile
├── requirements.txt
├── LICENSE  .gitignore  .gitattributes
├── Dockerfile  .dockerignore
├── .github/workflows/ci.yml
├── include/
│   ├── channel.h          # Channel interface + factory declaration
│   ├── timing.h           # now_ns(), cpu_relax()
│   ├── stats.h            # percentile/summary functions
│   └── sysutil.h          # pinning, rusage snapshot, unique names, write_all/read_all
├── src/
│   ├── pipe_channel.cpp
│   ├── fifo_channel.cpp
│   ├── mq_channel.cpp
│   ├── uds_channel.cpp
│   ├── shm_ring.h         # ring buffer + futex helpers (shared by 3 shm channels)
│   ├── shm_channel.cpp    # shm_spin, shm_futex, shm_hybrid
│   ├── factory.cpp        # make_channel(name)
│   ├── runner.cpp         # process model, ping-pong and stream benchmarks
│   └── main.cpp           # CLI
├── tests/
│   ├── testutil.h
│   ├── test_channels.cpp  # integrity tests for all channels
│   ├── test_shm_stress.cpp# stress test for the futex/hybrid rings
│   ├── test_cleanup.cpp   # no leaked resources
│   ├── test_stats.cpp
│   ├── test_analysis.py   # pytest: stats + recommender on synthetic CSV
├── scripts/
│   ├── run_experiments.py # experiment matrix orchestrator
│   ├── cleanup.sh         # remove leaked shm/fifo/mqueue objects with our prefix
│   ├── sanity_check_results.py
│   └── collect_for_review.sh
├── analysis/
│   ├── make_report.py     # plots + summary tables
│   └── recommend.py       # recommender CLI
├── results/               # raw.csv, system_info.json, summary.md, figures/, logs/
└── docs/
    ├── DESIGN.md  METHODOLOGY.md  RELATED_WORK.md  DECISIONS.md  RESULTS.md  PRESENTATION_OUTLINE.md
```

`make` targets: `all`, `venv`, `check` (build + all tests + line-ending check), `check-ci` (same with a shortened stress test), `bench-quick`, `bench-full`, `report`, `docker-build`, `docker-quick`, `clean`, `bundle`.

---

## 4. Channel interface (`include/channel.h`)

```cpp
struct Channel {
  // Called once in the parent BEFORE fork(). Creates all OS resources.
  virtual void setup(size_t max_msg_size) = 0;
  // Called in each process after fork() (e.g. close unused fds). role: 0 = parent(A), 1 = child(B).
  virtual void attach(int role) = 0;
  // Send/receive EXACTLY n bytes to/from the peer. Block until complete. Handle EINTR and partial IO.
  virtual void send(const void* buf, size_t n) = 0;
  virtual void recv(void* buf, size_t n) = 0;
  // Called in both processes at the end. Parent additionally unlinks names. Must be idempotent and leak-free.
  virtual void teardown(int role) = 0;
  virtual const char* name() const = 0;
  virtual bool chunked(size_t n) const { return false; } // true if n exceeds native per-message limit
  virtual ~Channel() = default;
};
std::unique_ptr<Channel> make_channel(const std::string& name);
// names: pipe, fifo, mq, uds, shm_spin, shm_futex, shm_hybrid
```

The channel is **bidirectional**: A->B and B->A are independent (never share one pipe/fd/eventfd for both directions).
All resource names use the prefix `/ipcbench_<pid>_<nonce>` so `scripts/cleanup.sh` can remove only our objects.

---

## 5. Mechanism specifications

- **pipe:** two `pipe()` pairs (one per direction), created pre-fork. Loop on partial `read`/`write`. Optional `F_SETPIPE_SZ` to 1 MiB, best effort; log whether it succeeded.
- **fifo:** two `mkfifo` files in `$TMPDIR` (or `/tmp`) with unique names (must be on the Linux filesystem; refuse any path under `/mnt/`); open order must avoid deadlock (use `O_RDWR` or a documented ordering). Unlink in teardown.
- **mq (POSIX message queue):** two queues. Default `msgsize_max` is 8192 and `maxmsg` is often 10, so messages larger than the native limit are **fragmented into chunks** of `min(8192, msgsize_max)`. `chunked(n)` returns true then. Read limits from `/proc/sys/fs/mqueue/*` and never require root. Reassemble exactly n bytes in `recv`.
- **uds:** `socketpair(AF_UNIX, SOCK_STREAM, 0)`. Loop on partial IO.
- **shm_*:** `shm_open` + `ftruncate` + `mmap(MAP_SHARED)` created pre-fork, `shm_unlink` immediately after mapping (the mapping stays valid for the forked child). Two single-producer/single-consumer **byte ring buffers** (one per direction), capacity default 256 KiB (power of two, configurable). `send(n)` writes n bytes in pieces as space frees; `recv(n)` reads n bytes in pieces as data arrives, so messages larger than capacity still work.

### Ring layout and synchronisation (shm_ring.h)

```cpp
struct Ring {
  alignas(64) std::atomic<uint64_t> head;       // total bytes written (producer-owned)
  alignas(64) std::atomic<uint64_t> tail;       // total bytes read (consumer-owned)
  alignas(64) std::atomic<uint32_t> data_seq;   // futex word the consumer sleeps on
  std::atomic<uint32_t> consumer_waiting;
  alignas(64) std::atomic<uint32_t> space_seq;  // futex word the producer sleeps on
  std::atomic<uint32_t> producer_waiting;
  alignas(64) uint8_t data[CAP];
};
```

Wait strategies (same ring, different waiting):
- **SPIN:** loop with `cpu_relax()` until condition holds. Never calls into the kernel.
- **FUTEX:** consumer: read `s = data_seq`; set `consumer_waiting=1`; re-check `head - tail`; if still empty call `futex_wait(&data_seq, s)` (raw `syscall(SYS_futex, ..., FUTEX_WAIT, ...)` WITHOUT `FUTEX_PRIVATE_FLAG`, since memory is shared across processes); clear `consumer_waiting`. Producer: after writing, `head.store(release)`, `atomic_thread_fence(seq_cst)`, `data_seq.fetch_add(1)`, and if `consumer_waiting` call `futex_wake`. Symmetric for space (`space_seq`, `producer_waiting`). The futex value comparison plus the re-check must make lost wake-ups impossible; document the reasoning in comments (Dekker-style ordering with seq_cst fences).
- **HYBRID:** spin up to `SPIN_ITERS` iterations (default 2000, overridable by env `IPCB_SPIN_ITERS` and CLI `--spin-iters`), then fall back to the FUTEX path.

---

## 6. Benchmark methodology (runner.cpp, main.cpp)

**Process model.** `main` creates the channel (`setup`), creates a separate **control socketpair** (used only for synchronisation and result passing, never for the measured traffic), `fork()`s, calls `attach(role)` in each process, and applies CPU pinning. Child (B) echoes in ping-pong or consumes in stream mode.

**Message format.** Minimum size 16 bytes. First 8 bytes = sequence number (uint64), next 8 bytes = checksum seed; the rest is a deterministic pattern. The receiver verifies sequence and first/last 8 bytes on every message (cheap, in-loop) and the full payload on the first and last iteration. Any mismatch = abort with `status=integrity_error`.

**Mode 1: `pingpong`.** A sends a message, B echoes it back; A records the round-trip time (RTT) per iteration in a preallocated `std::vector<uint64_t>` (no allocation in the loop). One-way latency is approximated as RTT/2 and **must be labelled as an approximation** in all outputs. First `warmup` iterations are discarded.

**Mode 2: `stream`.** A sends N messages one-way back to back; B receives; after the last message B sends a 1-byte ack on the control channel. Throughput = N / (time from first send to ack). Report msgs/s and MB/s.

**CPU cost.** Each process takes `getrusage(RUSAGE_SELF)` snapshots immediately before and after the measured phase. B sends its deltas to A over the control channel. Report: total user CPU seconds, total system CPU seconds (A+B), `cpu_pct` = (user+sys of A and B) / wall time x 100 (can exceed 100), voluntary and involuntary context switches (A+B) and `ctx_per_msg`.

**Pinning.** `--pin none|cross|same`. `cross` pins A and B to two different CPUs taken from the process's allowed CPU set (`--cpu-a`, `--cpu-b` override; if fewer than 2 CPUs are available, record `status=skipped_cpus`). `same` pins both to one CPU.

**Same-core spin caveat.** `shm_spin` with `--pin same` can stall because the waiting process spins until the scheduler preempts it. For that case cap iterations at 500 and record the real iteration count. Every run has a watchdog (default 60 s, `--timeout`): on timeout kill the child, clean up, and record `status=timeout`.

**Iteration defaults.** pingpong: 20000 iterations for sizes <= 64 KiB, 2000 for 1 MiB; warmup = 10%. stream: `N = clamp(256 MiB / size, 2000, 200000)`.

**CLI (one run = one process invocation = one CSV row):**
```
./build/ipcbench --mech shm_hybrid --mode pingpong --size 4096 --iters 20000 --warmup 2000 \
  --pin cross --run-id 3 --csv results/raw.csv [--cpu-a 2 --cpu-b 3] [--spin-iters 2000] [--timeout 60]
./build/ipcbench --list-mechs
```
Append each row with a single `write()` on an `O_APPEND` descriptor and take `flock` on a best-effort basis (ignore `ENOLCK`/`ENOSYS`, which can occur on Windows-mounted drives); the orchestrator runs invocations sequentially anyway. Write the header if the file is new.

**CSV schema (exact column order):**
`timestamp,git_commit,mech,mode,size_bytes,iters,warmup,pin,run_id,chunked,status,mean_ns,p50_ns,p90_ns,p99_ns,p999_ns,min_ns,max_ns,stddev_ns,msgs_per_s,mb_per_s,wall_s,cpu_user_s,cpu_sys_s,cpu_pct,vol_ctx,invol_ctx,ctx_per_msg`
For `stream` mode latency columns are empty. For `pingpong` the latency columns are RTT in ns.

**System info.** `scripts/run_experiments.py` writes `results/system_info.json`: kernel, distro, CPU model, core count, CPU governor if readable, whether running in a container/VM/WSL (detect `/proc/version`, `/.dockerenv`, `systemd-detect-virt` if present), compiler version, git commit.

---

## 7. Experiment matrix (scripts/run_experiments.py)

- Mechanisms: `pipe fifo mq uds shm_spin shm_futex shm_hybrid`
- Sizes (bytes): `16 256 4096 65536 1048576`
- Primary matrix: modes `pingpong` and `stream`, pin `cross`, 5 repetitions each, runs in a randomised order (fixed seed recorded in the CSV log) so thermal/background drift is not correlated with one mechanism.
- Secondary matrix: `pingpong`, pin `same`, 3 repetitions, all mechanisms, sizes `16 4096 65536`.
- Flags: `--quick` (sizes 16, 4096, 65536; 1 repetition; 20% of the iterations), `--full`, `--resume` (skip run_ids already in CSV), `--only-mech`, `--timeout`.
- Before every run call `scripts/cleanup.sh`. After each run check exit code and `status`. Print a one-line progress indicator, log details to `results/logs/`.
- WSL2 is the expected environment: print a one-line notice (not an error) that results are from a virtualised environment, and record it in `system_info.json`. Also warn, without aborting, if the governor is unreadable/not `performance` or fewer than 2 vCPUs are available. To reduce noise, the script should print a reminder at start: close browsers and other heavy apps, keep the laptop plugged in, and do not use the machine during the full run.

---

## 8. Analysis and report (analysis/make_report.py)

Read `results/raw.csv`, keep `status=ok` rows, aggregate repetitions with the **median** and show min/max as error bars. Produce (PNG, 150 dpi, clear titles/axes/units, log-scale where appropriate) in `results/figures/`:

1. `latency_vs_size.png` p50 RTT vs size per mechanism (log-log) with a p99 marker/band.
2. `throughput_vs_size.png` MB/s vs size per mechanism (stream mode).
3. `cpu_cost_vs_size.png` CPU time per message vs size.
4. `latency_vs_cpu_tradeoff.png` scatter: x = p50 RTT, y = CPU time per message, one point per (mechanism, size), annotated. **This is the headline figure.** Make sure shm_spin / shm_futex / shm_hybrid are visually connected.
5. `tail_ratio.png` p99/p50 per mechanism and size.
6. `ctx_switches_per_msg.png`.
7. `pinning_effect.png` same vs cross core for each mechanism (pingpong).

Also write `results/summary.md` with: a main table per size (p50, p99, MB/s, CPU/msg), the **crossover analysis** (smallest measured size where each shm variant beats pipe and uds on throughput by >= 20%, or "none found"), and the ranking per goal. Fill `docs/RESULTS.md` from real numbers only (generate sections automatically between `<!-- AUTO:START -->` and `<!-- AUTO:END -->` markers; leave human-written discussion outside them).

---

## 9. Recommender (analysis/recommend.py)

```
python analysis/recommend.py --size 4096 --pattern pingpong|stream \
    --goal min_latency|max_throughput|min_cpu|balanced [--max-p99-us 50] [--pin cross|same] [--top 3]
python analysis/recommend.py --export-rules   # writes results/recommendation_table.md
```
Logic:
- Load aggregated results. For a requested size, use the nearest measured sizes in log space and linearly interpolate in log-log space between the two neighbours (clamp outside the measured range and warn that the answer is an extrapolation).
- Score per goal: `min_latency` = p50 (tie-break p99); `max_throughput` = MB/s; `min_cpu` = CPU time per message; `balanced` = 0.4 x norm(p99) + 0.4 x norm(cpu per msg) + 0.2 x norm(ctx per msg), min-max normalised, weights defined as named constants and documented.
- Respect `--max-p99-us` as a hard filter.
- Output top-N as a table (numbers) plus one plain-English reason per pick (e.g. "no kernel copy and no system call on the fast path, but burns a full core while waiting"). Add a short static "practical notes" line per mechanism (e.g. mq has per-message size limits, uds supports multiple clients and fd passing, shm needs careful synchronisation and cleanup, fifo/pipe are simplest).
- Print a disclaimer that results are specific to the measured machine (print the system info from `results/system_info.json`).

---

## 10. Testing and self-verification (what you must run yourself)

`make check` must build everything and run, in this order, failing loudly:

1. `tests/test_stats.cpp`: percentile/summary correctness on known arrays.
2. `tests/test_channels.cpp`: for **each** of the 7 channels, sizes `{16, 17, 1000, 4096, 65536, 1048576}`: fork, 1000 echoed messages A->B->A with full payload verification, all channels must pass. Includes odd sizes to catch partial-IO bugs.
3. `tests/test_shm_stress.cpp`: `shm_futex` and `shm_hybrid`, 1,000,000 messages of random sizes 16..8192 streamed one-way with a running checksum compared at the end; repeat 10 times; each run under a 30 s timeout (a hang = failure = lost wake-up bug). Also a test with a tiny ring (4 KiB) and 64 KiB messages to force constant blocking on both sides.
4. `tests/test_cleanup.cpp`: after teardown (and after a child is killed mid-run), verify nothing with our prefix remains in `/dev/shm`, the FIFO directory, or `/dev/mqueue`. If `/dev/mqueue` is not mounted (common on WSL2), verify instead that `mq_open` of our queue names without `O_CREAT` fails with `ENOENT`.
5. `pytest tests/test_analysis.py`: synthetic CSV -> make_report runs without error, recommender returns the expected winner for hand-constructed data, interpolation and clamping work, filters work.

After the full run of `scripts/run_experiments.py`, run `scripts/sanity_check_results.py`, which must **fail** on: NaN/negative values, `p50 > p99`, rows with `status != ok` above 5%, missing combinations, throughput inconsistent with wall time. It must only **warn** on plausibility (e.g. shm_spin not beating pipe at 16 B cross-core, high variance with CV > 20% between repetitions, VM/WSL detected). Warnings are findings, not bugs: report them in `docs/RESULTS.md` under "Anomalies" instead of hiding them.

`scripts/collect_for_review.sh` creates `review_bundle.tar.gz` containing: `results/raw.csv`, `results/system_info.json`, `results/summary.md`, `results/figures/`, `results/logs/` (last 200 lines per file), the output of `make check`, and `git log --oneline | head -30`. The user can upload this single file for external review. Print its path and size at the end.

---

## 11. Documentation to write (all real, concise, student-presentable)

- `README.md`: CI badge, what/why (research gap in 5 lines), the WSL2/virtualisation disclaimer, quick start for WSL (`make venv`, `make check`, `make bench-quick`, `make bench-full`, `make report`, recommender example), Docker quick start (`make docker-build docker-quick`), repo layout, how to read the results, limitations, licence note (cite references; code written from scratch, no copied code).
- `docs/DESIGN.md`: architecture, interface, process model, ring buffer design with the futex protocol and why it cannot lose wake-ups, diagram in ASCII.
- `docs/METHODOLOGY.md`: every choice in section 6 and why (warm-up, pinning, ping-pong RTT/2 caveat, rusage, repetitions, randomised order, integrity checks, watchdog), and threats to validity (VM/WSL noise, frequency scaling, hyperthreads, single machine, `getrusage` granularity, fragmentation in mq).
- `docs/RELATED_WORK.md`: exactly these sources, described briefly in your own words, each with how this project differs. Do not add others unless you can open and verify them; mark any unverified item `TODO(verify)`:
  - goldsborough/ipc-bench (GitHub): ping-pong msgs/s table across mechanisms, self-described as old, no warm-up for shm.
  - rigtorp/ipc-bench (GitHub): crude latency/throughput for pipes, UDS, TCP, one-way shm.
  - rustyconover/memory-passing-speed-benchmark (GitHub): pipe vs shared-memory crossover (reports ~8 MB).
  - anttispitkanen/ipc-benchmark-testing (GitHub): IPC between Node.js Docker containers.
  - Venkataraman et al., as cited in "Smart Pointers and Shared Memory Synchronisation for Efficient IPC in ROS on an Autonomous Vehicle" (arXiv 2108.07085): shared memory best, comparable below 64 KB.
  - "A Dynamic Multi-Threaded Queuing Mechanism for Reducing the Inter-Process Communication Latency on Multi-Core Chips" (UT Arlington thesis, eLCRQ): futex block-when-necessary queue to cut spinning CPU cost.
  - Neon database discussion (GitHub issue #3184): busy-poll vs eventfd/futex tradeoff for shared-memory queues.
  - Linux kernel mailing list review of the Intel uintr-ipc-bench eventfd benchmark (2021): methodology pitfalls (shared eventfd, blocking mode).
  - Docker documentation on the IPC namespace (`--ipc`): containers have separate shared-memory namespaces.
  - A class report comparing a custom kernel-driver IPC and a shared-memory IPC (NTHU CSC5031 Topic03 Team06): similar academic setting, kernel driver approach not pursued here.
- `docs/RESULTS.md`: auto-generated tables/figures plus a human-readable discussion: what the data shows, why (copies, system calls, context switches, cache effects) stated as explanations/hypotheses supported by the measured data, anomalies, limitations.
- `docs/PRESENTATION_OUTLINE.md`: 8-10 slide outline (problem, gap, design, method, results with the tradeoff figure, recommender demo with 2 sample commands and their real outputs, limitations, future work) for the review.

---

## 12. Phases (do in order; stop-and-report points marked)

**Phase 0: scaffold.** Verify the environment (section 2A) and log it in `PROGRESS.md`. `git init -b main`, `.gitignore`, `.gitattributes`, `LICENSE`. Layout, Makefile (with `venv`), requirements, headers (`channel.h`, `timing.h`, `stats.h`, `sysutil.h`), `cleanup.sh`, `PROGRESS.md`, `docs/DECISIONS.md`. `make` builds an empty binary. Commit (and push if the remote is configured).

**Phase 1: simple channels.** pipe, fifo, uds, mq (with chunking) + factory + `test_stats.cpp` + `test_channels.cpp` for these four. All pass.

**Phase 2: shared memory.** `shm_ring.h`, the three `shm_*` channels, extend `test_channels.cpp`, add `test_shm_stress.cpp` and `test_cleanup.cpp`. All pass. **STOP and report** (status of each test, any design decisions, remaining risks).

**Phase 3: runner and CLI.** `runner.cpp`, `main.cpp`, control channel, pinning, rusage, CSV writing with flock, watchdog. Manual smoke test of every mechanism in both modes at 16 B and 64 KiB; show the CSV rows.

**Phase 4: experiment orchestrator.** `run_experiments.py`, `system_info.json`, `make bench-quick`. Run it and fix any hangs/failures. **STOP and report** (paste `head` of the CSV and the quick-run duration estimate for `--full`).

**Phase 5: full experiment.** `make bench-full` (use `--resume` if interrupted). Run `sanity_check_results.py`. Fix real bugs; record anomalies.

**Phase 6: analysis and recommender.** `make_report.py`, `recommend.py`, `test_analysis.py`, generate figures, `summary.md`, `recommendation_table.md`. Show two sample recommender runs.

**Phase 7: documentation, CI, Docker and bundle.** All docs in section 11 using real numbers, `collect_for_review.sh`, `make bundle`. Add `Dockerfile` + `make docker-build docker-quick` (runs the quick benchmark in a container; if Docker is unavailable, note it under "Needs user" and continue), and `.github/workflows/ci.yml`. Final `make check`, push, and confirm the CI run is green on GitHub if the user can see it. **STOP and report** with the bundle path.

**Phase 8 (optional, only if everything above passes and the user asks):**
- Docker comparison: run the same matrix inside a container (default IPC namespace vs `--ipc=host`) and compare with the native WSL2 results, reporting the overhead. Remember both share the same WSL2 VM kernel.
- Fan-in scenario: N producers -> 1 consumer for uds and shm_futex (logging-system pattern).
- TCP loopback baseline as an extra reference mechanism.

---

## 13. Definition of done

- [ ] `make check` passes on a clean checkout (all tests green, no leaked resources, no hangs).
- [ ] All 7 channels work in both modes and every message is integrity-verified.
- [ ] `results/raw.csv` has the full primary and secondary matrices with `status=ok` for at least 95% of the runs; the rest are explained.
- [ ] 7 figures and `summary.md` generated; the latency-vs-CPU figure clearly shows the shm spin/futex/hybrid tradeoff.
- [ ] Recommender works and its two sample outputs are in the docs.
- [ ] README, DESIGN, METHODOLOGY, RELATED_WORK, RESULTS, PRESENTATION_OUTLINE written; no invented numbers; all `TODO(results)` resolved.
- [ ] `review_bundle.tar.gz` can be produced with `make bundle`.
- [ ] Everything builds and runs through WSL2 Ubuntu from the project folder on D:, with no CRLF files, a working venv at `$(VENV)`, and no temp/FIFO files outside `/tmp`.
- [ ] README has the CI badge, the WSL/virtualisation disclaimer, a WSL quick start and a Docker quick start.
- [ ] `Dockerfile` builds and `make docker-quick` runs the quick benchmark (or the reason it could not is logged under "Needs user").
- [ ] All phases are committed with conventional messages and pushed to GitHub; the CI workflow passes `make check-ci`.
