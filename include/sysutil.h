#pragma once
#include <cstddef>
#include <cstdint>
#include <unistd.h>
#include <cerrno>
#include <stdexcept>
#include <string>
#include <sched.h>
#include <vector>

inline void write_all(int fd, const void* p, size_t n) {
  const char* b = static_cast<const char*>(p);
  while (n) { ssize_t r = write(fd, b, n); if (r < 0 && errno == EINTR) continue; if (r <= 0) throw std::runtime_error("write failed"); b += r; n -= size_t(r); }
}
inline void read_all(int fd, void* p, size_t n) {
  char* b = static_cast<char*>(p);
  while (n) { ssize_t r = read(fd, b, n); if (r < 0 && errno == EINTR) continue; if (r <= 0) throw std::runtime_error("read failed"); b += r; n -= size_t(r); }
}
inline std::string unique_name(const char* prefix) {
  return std::string(prefix) + std::to_string(getpid()) + "_" + std::to_string(reinterpret_cast<uintptr_t>(&prefix));
}
inline std::vector<int> allowed_cpus() {
  cpu_set_t set; CPU_ZERO(&set);
  if (sched_getaffinity(0, sizeof(set), &set) != 0) return {};
  std::vector<int> out; for (int i = 0; i < CPU_SETSIZE; ++i) if (CPU_ISSET(i, &set)) out.push_back(i);
  return out;
}
inline bool pin_cpu(int cpu) {
  cpu_set_t set; CPU_ZERO(&set); CPU_SET(cpu, &set);
  return sched_setaffinity(0, sizeof(set), &set) == 0;
}
