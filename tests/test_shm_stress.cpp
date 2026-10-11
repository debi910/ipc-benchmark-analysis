#include "channel.h"
#include "sysutil.h"
#include <cassert>
#include <cstdint>
#include <iostream>
#include <random>
#include <sys/wait.h>
#include <unistd.h>
#include <vector>

static constexpr size_t REPEATS =
#ifdef IPC_STRESS_REPEATS
  IPC_STRESS_REPEATS;
#else
  3;
#endif
static constexpr size_t MESSAGES =
#ifdef IPC_STRESS_MESSAGES
  IPC_STRESS_MESSAGES;
#else
  200000;
#endif

static void stress(const char* name) {
  auto c = make_channel(name); c->setup(8192);
  int control[2]; assert(pipe(control) == 0);
  pid_t child = fork(); assert(child >= 0);
  if (!child) {
    close(control[0]); c->attach(1); std::mt19937 rng(7);
    uint64_t checksum = 0; std::vector<uint8_t> b(8192);
    for (size_t i = 0; i < MESSAGES; ++i) {
      size_t n = 16 + (rng() % (8192 - 15)); c->recv(b.data(), n);
      for (size_t j = 0; j < n; ++j) checksum += b[j];
    }
    write_all(control[1], &checksum, sizeof(checksum)); c->teardown(1); _exit(0);
  }
  close(control[1]); c->attach(0); std::mt19937 rng(7);
  uint64_t expected = 0; std::vector<uint8_t> b(8192, 0x5a);
  for (size_t i = 0; i < MESSAGES; ++i) {
    size_t n = 16 + (rng() % (8192 - 15));
    for (size_t j = 0; j < n; ++j) expected += b[j];
    c->send(b.data(), n);
  }
  uint64_t actual = 0; assert(read(control[0], &actual, sizeof(actual)) == sizeof(actual));
  int status = 0; waitpid(child, &status, 0); assert(WIFEXITED(status) && actual == expected);
  c->teardown(0);
}

int main() {
  for (const char* n : {"shm_futex", "shm_hybrid"})
    for (size_t r = 0; r < REPEATS; ++r) { stress(n); std::cout << n << " repeat " << r + 1 << "/" << REPEATS << " PASS\n"; }
}
