#include <cassert>
#include <cstdio>
#include <fstream>
#include <string>
#include <sys/wait.h>
#include <unistd.h>

int main() {
  const char* csv = "/tmp/ipcbench_timeout_test.csv";
  unlink(csv);
  pid_t pid = fork();
  assert(pid >= 0);
  if (pid == 0) {
    execl("./build/ipcbench", "./build/ipcbench",
          "--mech", "shm_spin", "--mode", "pingpong", "--size", "16",
          "--iters", "20000", "--warmup", "2000", "--pin", "same",
          "--no-same-cap", "--timeout", "2", "--csv", csv, nullptr);
    _exit(127);
  }
  int status = 0;
  assert(waitpid(pid, &status, 0) == pid);
  assert(WIFEXITED(status) && WEXITSTATUS(status) != 0);
  std::ifstream input(csv);
  std::string line, last;
  while (std::getline(input, line)) if (!line.empty()) last = line;
  assert(last.find(",timeout,") != std::string::npos);
  unlink(csv);
}
