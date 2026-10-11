#include "channel.h"
#include "sysutil.h"
#include <sys/stat.h>
#include <fcntl.h>
#include <unistd.h>
#include <stdexcept>
class FifoChannel final : public Channel {
 std::string path[2]; int fd[2]{-1,-1}; int role=0;
 public:
 void setup(size_t) override { for(int i=0;i<2;i++){path[i]=unique_name("/tmp/ipcbench_fifo_")+"_"+std::to_string(i); if(mkfifo(path[i].c_str(),0600)) throw std::runtime_error("mkfifo"); fd[i]=open(path[i].c_str(),O_RDWR); if(fd[i]<0) throw std::runtime_error("fifo open");} }
 void attach(int r) override {role=r;}
 void send(const void*p,size_t n) override {write_all(fd[role],p,n);}
 void recv(void*p,size_t n) override {read_all(fd[1-role],p,n);}
 void teardown(int) override {for(int i=0;i<2;i++){if(fd[i]>=0)close(fd[i]);if(!path[i].empty())unlink(path[i].c_str());fd[i]=-1;}}
 const char* name()const override{return "fifo";}
};
std::unique_ptr<Channel> make_fifo(){return std::make_unique<FifoChannel>();}
