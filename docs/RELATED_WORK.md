# Related work

- **goldsborough/ipc-bench (GitHub).** Reports ping-pong messages-per-second
  tables across IPC mechanisms and describes itself as old. This project adds
  warm-up, integrity checks, CPU/context-switch/tail metrics, same-core
  pinning, shared-memory futex variants, and a recommendation workflow.
- **rigtorp/ipc-bench (GitHub).** Provides a compact latency/throughput
  comparison for pipes, UDS, TCP, and one-way shared memory. This project uses
  a common bidirectional interface, includes message queues and FIFOs, tests
  both stream and ping-pong behavior, and records tail and scheduling metrics.
- **rustyconover/memory-passing-speed-benchmark (GitHub).** Studies a pipe versus
  shared-memory crossover and reports a crossover around 8 MB. This project
  measures more mechanisms and sizes, tests synchronization strategies, and
  reports a measured crossover analysis rather than assuming that threshold.
- **anttispitkanen/ipc-benchmark-testing (GitHub).** Measures IPC between
  Node.js Docker containers. This project is a native C++ Linux/WSL2 study
  focused on process-local IPC primitives and documents virtualization limits.
- **Venkataraman et al., “Smart Pointers and Shared Memory Synchronisation for
  Efficient IPC in ROS on an Autonomous Vehicle,” arXiv:2108.07085.** The
  cited work reports shared memory as strongest overall and comparable behavior
  below 64 KB. This project tests a different workload matrix and treats those
  statements as context, not as a claim that the present machine proves the
  same mechanism-level cause.

The descriptions above follow the sources specified in the project brief; no
additional sources are used here.
