#pragma once
#include <memory>
#include <string>
struct ChannelDiagnostics {
  uint64_t spin_loops = 0;
  uint64_t futex_waits = 0;
  uint64_t futex_wakes = 0;
};
struct Channel {
  virtual void setup(size_t max_msg_size) = 0;
  virtual void attach(int role) = 0;
  virtual void send(const void* buf, size_t n) = 0;
  virtual void recv(void* buf, size_t n) = 0;
  virtual void teardown(int role) = 0;
  virtual const char* name() const = 0;
  virtual bool chunked(size_t) const { return false; }
  virtual ChannelDiagnostics diagnostics() const { return {}; }
  virtual ~Channel() = default;
};
std::unique_ptr<Channel> make_channel(const std::string& name);
