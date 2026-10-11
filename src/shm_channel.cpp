#include "channel.h"
#include "shm_ring.h"
#include <algorithm>
#include <cstring>
#include <fcntl.h>
#include <new>
#include <sys/mman.h>
#include <stdexcept>
#include <string>
#include <unistd.h>

class ShmChannel final : public Channel {
  ShmRing* rings_[2]{};
  int role_ = 0;
  std::string mode_;
  bool use_futex() const { return mode_ != "shm_spin"; }
  bool hybrid() const { return mode_ == "shm_hybrid"; }

  void wait_for(ShmRing* r, bool writing) {
    unsigned spins = 0;
    const unsigned limit = hybrid() ? 2000U : 0U;
    while (hybrid() && spins++ < limit) {
      r->spin_loops.fetch_add(1, std::memory_order_relaxed);
      uint64_t h = r->head.load(std::memory_order_acquire);
      uint64_t t = r->tail.load(std::memory_order_acquire);
      if (writing ? (SHM_RING_CAPACITY - (h - t) != 0) : (h - t != 0)) return;
      cpu_relax();
    }
    if (!use_futex()) {
      r->spin_loops.fetch_add(1, std::memory_order_relaxed);
      cpu_relax();
      return;
    }
    auto* seq = writing ? &r->space_seq : &r->data_seq;
    auto* waiting = writing ? &r->producer_waiting : &r->consumer_waiting;
    uint32_t expected = seq->load(std::memory_order_acquire);
    waiting->store(1, std::memory_order_seq_cst);
    std::atomic_thread_fence(std::memory_order_seq_cst);
    uint64_t h = r->head.load(std::memory_order_acquire);
    uint64_t t = r->tail.load(std::memory_order_acquire);
    bool blocked = writing ? (SHM_RING_CAPACITY - (h - t) == 0) : (h - t == 0);
    if (blocked) {
      r->futex_waits.fetch_add(1, std::memory_order_relaxed);
      futex_wait(seq, expected);
    }
    waiting->store(0, std::memory_order_seq_cst);
  }

  void transfer(void* out, const void* in, size_t n, bool writing) {
    ShmRing* r = rings_[writing ? role_ : 1 - role_];
    auto* dst = static_cast<uint8_t*>(out);
    auto* src = static_cast<const uint8_t*>(in);
    while (n) {
      uint64_t h = r->head.load(std::memory_order_acquire);
      uint64_t t = r->tail.load(std::memory_order_acquire);
      uint64_t available = writing ? SHM_RING_CAPACITY - (h - t) : h - t;
      if (!available) { wait_for(r, writing); continue; }
      size_t count = std::min<uint64_t>(n, available);
      size_t at = size_t((writing ? h : t) % SHM_RING_CAPACITY);
      size_t first = std::min(count, SHM_RING_CAPACITY - at);
      if (writing) {
        std::memcpy(r->data + at, src, first);
        if (first < count) std::memcpy(r->data, src + first, count - first);
        r->head.store(h + count, std::memory_order_release);
        r->data_seq.fetch_add(1, std::memory_order_seq_cst);
        if (r->consumer_waiting.load(std::memory_order_seq_cst)) {
          r->futex_wakes.fetch_add(1, std::memory_order_relaxed);
          futex_wake(&r->data_seq);
        }
        src += count;
      } else {
        std::memcpy(dst, r->data + at, first);
        if (first < count) std::memcpy(dst + first, r->data, count - first);
        r->tail.store(t + count, std::memory_order_release);
        r->space_seq.fetch_add(1, std::memory_order_seq_cst);
        if (r->producer_waiting.load(std::memory_order_seq_cst)) {
          r->futex_wakes.fetch_add(1, std::memory_order_relaxed);
          futex_wake(&r->space_seq);
        }
        dst += count;
      }
      n -= count;
    }
  }

 public:
  explicit ShmChannel(std::string mode) : mode_(std::move(mode)) {}
  void setup(size_t) override {
    for (int i = 0; i < 2; ++i) {
      std::string name = "/ipcbench_" + std::to_string(getpid()) + "_" +
                         std::to_string(reinterpret_cast<uintptr_t>(this)) +
                         "_" + std::to_string(i);
      int fd = shm_open(name.c_str(), O_CREAT | O_EXCL | O_RDWR, 0600);
      if (fd < 0) throw std::runtime_error("shm_open");
      if (ftruncate(fd, sizeof(ShmRing)) != 0) {
        close(fd); shm_unlink(name.c_str()); throw std::runtime_error("ftruncate");
      }
      void* p = mmap(nullptr, sizeof(ShmRing), PROT_READ | PROT_WRITE,
                     MAP_SHARED, fd, 0);
      close(fd);
      shm_unlink(name.c_str());
      if (p == MAP_FAILED) throw std::runtime_error("mmap");
      rings_[i] = new (p) ShmRing();
    }
  }
  void attach(int r) override { role_ = r; }
  void send(const void* p, size_t n) override { transfer(nullptr, p, n, true); }
  void recv(void* p, size_t n) override { transfer(p, nullptr, n, false); }
  void teardown(int) override {
    for (auto& r : rings_) if (r) { munmap(r, sizeof(ShmRing)); r = nullptr; }
  }
  const char* name() const override { return mode_.c_str(); }
  ChannelDiagnostics diagnostics() const override {
    ChannelDiagnostics d;
    for (auto* r : rings_) if (r) {
      d.spin_loops += r->spin_loops.load();
      d.futex_waits += r->futex_waits.load();
      d.futex_wakes += r->futex_wakes.load();
    }
    return d;
  }
};

std::unique_ptr<Channel> make_shm(const std::string& n) {
  return std::make_unique<ShmChannel>(n);
}
