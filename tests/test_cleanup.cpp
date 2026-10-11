#include "channel.h"
#include <cassert>
#include <csignal>
#include <dirent.h>
#include <iostream>
#include <sys/wait.h>
#include <thread>
#include <chrono>
#include <unistd.h>

static bool has_prefix(const char* dir, const char* prefix) {
  DIR* d = opendir(dir); if (!d) return false;
  bool found = false; while (auto* e = readdir(d))
    if (std::string(e->d_name).rfind(prefix, 0) == 0) found = true;
  closedir(d); return found;
}
static void verify_clean() {
  assert(!has_prefix("/dev/shm", "ipcbench_"));
  assert(!has_prefix("/tmp", "ipcbench_fifo_"));
  assert(!has_prefix("/dev/mqueue", "ipcbench_mq_"));
}
static void normal(const char* name) {
  auto c = make_channel(name); c->setup(4096); c->teardown(0); verify_clean();
}
static void killed(const char* name) {
  auto c = make_channel(name); c->setup(4096); pid_t p = fork(); assert(p >= 0);
  if (!p) { c->attach(1); std::this_thread::sleep_for(std::chrono::seconds(10)); _exit(0); }
  c->attach(0); std::this_thread::sleep_for(std::chrono::milliseconds(20));
  kill(p, SIGKILL); waitpid(p, nullptr, 0); c->teardown(0); verify_clean();
}
int main() {
  for (const char* n : {"pipe","fifo","mq","uds","shm_spin","shm_futex","shm_hybrid"}) {
    normal(n); killed(n); std::cout << n << ": cleanup PASS (normal + killed child)\n";
  }
}
