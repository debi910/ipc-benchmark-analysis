#include "channel.h"
#include "sysutil.h"
#include <sys/socket.h>
#include <stdexcept>
class UdsChannel final : public Channel {
 int fd[2]{-1,-1}; int role=0;
 public:
 void setup(size_t) override { if (socketpair(AF_UNIX, SOCK_STREAM, 0, fd)) throw std::runtime_error("socketpair"); }
 void attach(int r) override { role=r; close(fd[1-r]); }
 void send(const void* p,size_t n) override { write_all(fd[role],p,n); }
 void recv(void* p,size_t n) override { read_all(fd[role],p,n); }
 void teardown(int) override { if(fd[0]>=0) close(fd[0]); if(fd[1]>=0) close(fd[1]); fd[0]=fd[1]=-1; }
 const char* name() const override { return "uds"; }
};
std::unique_ptr<Channel> make_uds(){return std::make_unique<UdsChannel>();}
