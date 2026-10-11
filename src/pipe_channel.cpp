#include "channel.h"
#include "sysutil.h"
#include <unistd.h>
#include <stdexcept>
class PipeChannel final : public Channel {
  int fds[2][2]{{-1,-1},{-1,-1}};
  int role = 0;
 public:
  void setup(size_t) override { if (pipe(fds[0]) || pipe(fds[1])) throw std::runtime_error("pipe"); }
  void attach(int r) override { role = r; close(fds[r][0]); close(fds[1-r][1]); }
  void send(const void* p, size_t n) override { write_all(fds[role][1], p, n); }
  void recv(void* p, size_t n) override { read_all(fds[1-role][0], p, n); }
  void teardown(int) override { for (auto& x : fds) { if (x[0]>=0) { close(x[0]); x[0]=-1; } if (x[1]>=0) { close(x[1]); x[1]=-1; } } }
  const char* name() const override { return "pipe"; }
};
std::unique_ptr<Channel> make_pipe() { return std::make_unique<PipeChannel>(); }
