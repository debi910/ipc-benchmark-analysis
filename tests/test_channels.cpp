#include "channel.h"
#include <cassert>
#include <chrono>
#include <csignal>
#include <iostream>
#include <sys/wait.h>
#include <thread>
#include <vector>
void run_echo(Channel&,size_t,size_t);
static ChannelDiagnostics blocking_probe(const char* name) {
  auto c = make_channel(name); c->setup(1 << 20);
  pid_t child = fork(); assert(child >= 0);
  if (!child) {
    c->attach(1); std::this_thread::sleep_for(std::chrono::milliseconds(100));
    std::vector<char> b(1 << 20); c->recv(b.data(), b.size()); c->teardown(1); _exit(0);
  }
  c->attach(0); std::vector<char> b(1 << 20, 'x'); c->send(b.data(), b.size());
  int status = 0; waitpid(child, &status, 0); auto d = c->diagnostics(); c->teardown(0); return d;
}
int main() {
  for (const char* n : {"pipe","fifo","mq","uds","shm_spin","shm_futex","shm_hybrid"}) {
    auto c = make_channel(n); run_echo(*c,16,20); run_echo(*c,4096,5);
    std::cout << n << ": PASS (16x20, 4096x5)\n";
  }
  auto spin = blocking_probe("shm_spin");
  auto futex = blocking_probe("shm_futex");
  auto hybrid = blocking_probe("shm_hybrid");
  assert(spin.futex_waits == 0 && spin.futex_wakes == 0);
  assert(futex.futex_waits > 0 && futex.futex_wakes > 0);
  assert(hybrid.spin_loops > 0 && hybrid.futex_waits > 0);
  std::cout << "diagnostics: PASS (spin waits=0, futex waits>0, hybrid spin+futex)\n";
}
