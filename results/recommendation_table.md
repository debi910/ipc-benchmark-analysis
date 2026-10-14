# Recommendation table

| Size | Pattern | Goal | Recommended mechanism |
|---:|---|---|---|
| 16 | pingpong | min_latency | shm_hybrid |
| 16 | pingpong | max_throughput | shm_hybrid |
| 16 | pingpong | min_cpu | shm_hybrid |
| 16 | pingpong | balanced | shm_hybrid |
| 16 | stream | min_latency | unavailable |
| 16 | stream | max_throughput | shm_hybrid |
| 16 | stream | min_cpu | shm_hybrid |
| 16 | stream | balanced | unavailable |
| 256 | pingpong | min_latency | shm_hybrid |
| 256 | pingpong | max_throughput | shm_hybrid |
| 256 | pingpong | min_cpu | shm_hybrid |
| 256 | pingpong | balanced | shm_hybrid |
| 256 | stream | min_latency | unavailable |
| 256 | stream | max_throughput | shm_hybrid |
| 256 | stream | min_cpu | shm_hybrid |
| 256 | stream | balanced | unavailable |
| 4096 | pingpong | min_latency | shm_hybrid |
| 4096 | pingpong | max_throughput | shm_hybrid |
| 4096 | pingpong | min_cpu | shm_hybrid |
| 4096 | pingpong | balanced | shm_hybrid |
| 4096 | stream | min_latency | unavailable |
| 4096 | stream | max_throughput | shm_spin |
| 4096 | stream | min_cpu | shm_spin |
| 4096 | stream | balanced | unavailable |
| 65536 | pingpong | min_latency | shm_spin |
| 65536 | pingpong | max_throughput | shm_spin |
| 65536 | pingpong | min_cpu | shm_spin |
| 65536 | pingpong | balanced | shm_spin |
| 65536 | stream | min_latency | unavailable |
| 65536 | stream | max_throughput | shm_spin |
| 65536 | stream | min_cpu | shm_futex |
| 65536 | stream | balanced | unavailable |
| 1048576 | pingpong | min_latency | shm_spin |
| 1048576 | pingpong | max_throughput | shm_spin |
| 1048576 | pingpong | min_cpu | shm_futex |
| 1048576 | pingpong | balanced | shm_spin |
| 1048576 | stream | min_latency | unavailable |
| 1048576 | stream | max_throughput | shm_spin |
| 1048576 | stream | min_cpu | shm_futex |
| 1048576 | stream | balanced | unavailable |
