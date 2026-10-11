#include "channel.h"
#include "sysutil.h"
#include <mqueue.h>
#include <fcntl.h>
#include <sys/stat.h>
#include <stdexcept>
#include <algorithm>
class MqChannel final : public Channel {
 mqd_t q[2]{(mqd_t)-1,(mqd_t)-1}; std::string n[2]; size_t chunk=8192; int role=0;
 public:
 void setup(size_t) override { mq_attr a{}; a.mq_maxmsg=10;a.mq_msgsize=8192; for(int i=0;i<2;i++){n[i]=unique_name("/ipcbench_mq_")+"_"+std::to_string(i);q[i]=mq_open(n[i].c_str(),O_CREAT|O_RDWR,0600,&a);if(q[i]==(mqd_t)-1)throw std::runtime_error("mq_open");} }
 void attach(int r)override{role=r;}
 void send(const void*p,size_t z)override{const char*b=(const char*)p;while(z){size_t k=std::min(z,chunk);if(mq_send(q[role],b,k,0))throw std::runtime_error("mq_send");b+=k;z-=k;}}
 void recv(void*p,size_t z)override{char*b=(char*)p;while(z){size_t k=std::min(z,chunk);unsigned pr;ssize_t r=mq_receive(q[1-role],b,8192,&pr);if(r<0||size_t(r)!=k)throw std::runtime_error("mq_receive");b+=k;z-=k;}}
 void teardown(int)override{for(int i=0;i<2;i++){if(q[i]!=(mqd_t)-1)mq_close(q[i]);if(!n[i].empty())mq_unlink(n[i].c_str());q[i]=(mqd_t)-1;}}
 const char*name()const override{return "mq";} bool chunked(size_t z)const override{return z>chunk;}
};
std::unique_ptr<Channel> make_mq(){return std::make_unique<MqChannel>();}
