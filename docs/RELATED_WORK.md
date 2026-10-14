# Related work

- **goldsborough/ipc-bench (GitHub).** Reports ping-pong messages-per-second
  tables across IPC mechanisms and describes itself as old. This project adds
  warm-up, integrity checks, CPU/context-switch/tail metrics, same-core
  pinning, shared-memory futex variants, and a recommendation workflow.
- **rigtorp/ipc-bench (GitHub).** Provides a compact latency/throughput
  comparison for pipes, UDS, TCP, and one-way shared memory. This project uses
  a common bidirectional interface, includes message queues and FIFOs, tests
  both stream and ping-pong behavior, and records tail and scheduling metrics.
- **rustyconover/memory-passing-speed-benchmark (GitHub).** Studies a pipe
  versus shared-memory comparison and reports a crossover around 8 MB. In this
  project's measured sizes, no crossover was observed: shared memory led pipe
  at every measured size. The workloads, ring protocol, and host differ.
- **anttispitkanen/ipc-benchmark-testing (GitHub).** Measures IPC between
  Node.js Docker containers. This project is a native C++ Linux/WSL2 study
  focused on process-local IPC primitives and documents virtualization limits.
- **Venkataraman et al., “Smart Pointers and Shared Memory Synchronisation for
  Efficient IPC in ROS on an Autonomous Vehicle,” arXiv:2108.07085.** The
  cited work reports shared memory as strongest overall and comparable behavior
  below 64 KB. This project tests a different workload matrix and treats that
  statement as context, not as a claim that the present machine proves the same
  mechanism-level cause.
- **“A Dynamic Multi-Threaded Queuing Mechanism for Reducing the Inter-Process
  Communication Latency on Multi-Core Chips” (UT Arlington thesis, eLCRQ).**
  The brief identifies its futex-block-when-necessary queue as relevant to
  reducing spin CPU cost. TODO(verify): obtain and check the primary thesis
  text before making a stronger comparison.
- **Neon database GitHub issue #3184.** Discusses busy-polling versus eventfd/
  futex trade-offs for shared-memory queues. TODO(verify): verify the issue
  contents and exact conclusions from the primary discussion.
- **Linux kernel mailing-list review of the Intel uintr-ipc-bench eventfd
  benchmark (2021).** Highlights methodology pitfalls such as shared eventfd
  state and blocking-mode choices. TODO(verify): verify the thread and cited
  benchmark details.
- **Docker documentation for `--ipc`.** Documents that containers normally
  have separate IPC namespaces and can share the host namespace with
  `--ipc=host`. This project adds Docker targets but has not yet run the
  comparison.
- **NTHU CSC5031 Topic03 Team06 class report.** Compares custom
  kernel-driver IPC with shared-memory IPC in an academic setting; this project
  does not pursue a kernel driver. TODO(verify): obtain the report and confirm
  the exact measurements.
