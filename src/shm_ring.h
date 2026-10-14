#pragma once
#include "timing.h"
#include "sysutil.h"
#include <atomic>
#include <sys/mman.h>
#include <linux/futex.h>
#include <sys/syscall.h>
#include <unistd.h>
#include <cerrno>
#include <time.h>
#ifndef IPCB_RING_CAPACITY
#define IPCB_RING_CAPACITY 262144
#endif
constexpr size_t SHM_RING_CAPACITY = IPCB_RING_CAPACITY;
struct ShmRing {
  alignas(64) std::atomic<uint64_t> head{0}, tail{0};
  alignas(64) std::atomic<uint32_t> data_seq{0};
  std::atomic<uint32_t> consumer_waiting{0};
  alignas(64) std::atomic<uint32_t> space_seq{0};
  std::atomic<uint32_t> producer_waiting{0};
  std::atomic<uint64_t> spin_loops{0}, futex_waits{0}, futex_wakes{0};
  alignas(64) uint8_t data[SHM_RING_CAPACITY];
};
inline int futex_wait(std::atomic<uint32_t>* p, uint32_t v) {
  const timespec timeout{0, 100000000};
  return syscall(SYS_futex, reinterpret_cast<uint32_t*>(p), FUTEX_WAIT, v,
                 &timeout, nullptr, 0);
}
inline int futex_wake(std::atomic<uint32_t>* p) {
  return syscall(SYS_futex, reinterpret_cast<uint32_t*>(p), FUTEX_WAKE, 1,
                 nullptr, nullptr, 0);
}
