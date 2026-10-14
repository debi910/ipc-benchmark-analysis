# Measured summary

All values are medians over repetitions; source: `results/raw.csv`.

## Cross-core ping-pong at 16 bytes

| Mechanism | p50 RTT (ns) | p99 RTT (ns) | CPU/msg (ns) | ctx/msg |
|---|---:|---:|---:|---:|
| shm_hybrid | 311.0 | 410.0 | 804.9 | 0.000 |
| shm_spin | 367.0 | 497.0 | 873.5 | 0.000 |
| shm_futex | 36433.5 | 74571.0 | 36409.6 | 2.190 |
| uds | 39239.5 | 103044.0 | 41427.9 | 2.324 |
| mq | 40506.5 | 100089.0 | 43323.2 | 2.186 |
| pipe | 43844.0 | 92549.0 | 44244.4 | 2.192 |
| fifo | 47323.5 | 98781.2 | 46577.2 | 2.191 |

## Cross-core ping-pong at 256 bytes

| Mechanism | p50 RTT (ns) | p99 RTT (ns) | CPU/msg (ns) | ctx/msg |
|---|---:|---:|---:|---:|
| shm_hybrid | 374.0 | 482.0 | 1102.8 | 0.000 |
| shm_spin | 422.0 | 483.0 | 1158.6 | 0.000 |
| uds | 36434.0 | 97805.0 | 39370.6 | 2.282 |
| fifo | 37210.5 | 80326.2 | 36958.7 | 2.193 |
| shm_futex | 37451.0 | 76946.4 | 37373.2 | 2.189 |
| mq | 39574.0 | 87813.1 | 39585.8 | 2.190 |
| pipe | 44380.0 | 89894.1 | 44248.6 | 2.192 |

## Cross-core ping-pong at 4096 bytes

| Mechanism | p50 RTT (ns) | p99 RTT (ns) | CPU/msg (ns) | ctx/msg |
|---|---:|---:|---:|---:|
| shm_hybrid | 1482.0 | 2129.1 | 5991.9 | 0.000 |
| shm_spin | 1491.0 | 2168.1 | 6199.7 | 0.000 |
| uds | 34549.0 | 86672.0 | 41463.4 | 2.724 |
| pipe | 36756.0 | 78435.6 | 37673.2 | 2.194 |
| shm_futex | 39252.0 | 78833.0 | 39236.2 | 2.191 |
| mq | 41596.0 | 80566.1 | 42295.9 | 2.193 |
| fifo | 42128.5 | 90878.6 | 42754.7 | 2.194 |

## Cross-core ping-pong at 65536 bytes

| Mechanism | p50 RTT (ns) | p99 RTT (ns) | CPU/msg (ns) | ctx/msg |
|---|---:|---:|---:|---:|
| shm_spin | 12974.0 | 22321.3 | 67887.0 | 0.000 |
| shm_hybrid | 13701.0 | 28824.6 | 77567.3 | 0.001 |
| shm_futex | 54429.0 | 114572.0 | 80440.4 | 2.194 |
| pipe | 71027.5 | 136734.0 | 98342.8 | 2.197 |
| fifo | 72784.0 | 142303.0 | 98746.8 | 2.197 |
| mq | 76313.0 | 166826.0 | 128264.0 | 2.228 |
| uds | 86154.5 | 179698.0 | 130363.4 | 4.418 |

## Cross-core ping-pong at 1048576 bytes

| Mechanism | p50 RTT (ns) | p99 RTT (ns) | CPU/msg (ns) | ctx/msg |
|---|---:|---:|---:|---:|
| shm_spin | 214160.0 | 367975.0 | 1302165.0 | 0.000 |
| shm_hybrid | 340118.0 | 697975.0 | 1218184.5 | 1.358 |
| uds | 380286.0 | 913635.0 | 1114046.5 | 14.030 |
| mq | 613700.0 | 1204010.0 | 1506085.0 | 10.738 |
| shm_futex | 638788.0 | 917257.0 | 1026635.5 | 15.358 |
| pipe | 1826590.0 | 3210030.0 | 2297871.5 | 67.876 |
| fifo | 1840800.0 | 3062590.0 | 2247642.5 | 67.681 |

## Crossover analysis

Smallest measured stream size where a shared-memory variant reaches at least 20% more throughput than both pipe and UDS:
- `shm_futex`: 16
- `shm_hybrid`: 16
- `shm_spin`: 16
