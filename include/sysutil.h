#pragma once
#include <cstddef>
#include <cstdint>
#include <unistd.h>
#include <cerrno>
#include <stdexcept>
#include <string>

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
