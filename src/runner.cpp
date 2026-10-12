#include "channel.h"
#include "stats.h"
#include "sysutil.h"
#include "timing.h"
#include <algorithm>
#include <csignal>
#include <cstring>
#include <ctime>
#include <fcntl.h>
#include <sstream>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <sys/socket.h>
#include <sys/file.h>
#include <sys/resource.h>
#include <sys/wait.h>
#include <unistd.h>
#include <vector>

struct Usage { long user_us, sys_us, vol, invol; };
static Usage usage() {
  rusage r{}; getrusage(RUSAGE_SELF, &r);
  return {r.ru_utime.tv_sec*1000000L+r.ru_utime.tv_usec,
          r.ru_stime.tv_sec*1000000L+r.ru_stime.tv_usec,
          r.ru_nvcsw, r.ru_nivcsw};
}
static Usage delta(Usage a, Usage b) { return {b.user_us-a.user_us,b.sys_us-a.sys_us,b.vol-a.vol,b.invol-a.invol}; }
struct ChildReport { Usage u{}; int ok = 1; };
static volatile sig_atomic_t timed_out = 0;
static volatile sig_atomic_t watched_pid = -1;
static void alarm_handler(int) { timed_out = 1; if (watched_pid > 0) kill(watched_pid, SIGKILL); }

void run_echo(Channel& c, size_t size, size_t iters) {
  c.setup(size); int ctl[2]; if (pipe(ctl)) throw std::runtime_error("control pipe");
  pid_t pid=fork(); if(pid<0) throw std::runtime_error("fork");
  if(!pid){ close(ctl[0]); c.attach(1); std::vector<char>b(size);
    for(size_t i=0;i<iters;i++){c.recv(b.data(),size);c.send(b.data(),size);}
    c.teardown(1); _exit(0); }
  close(ctl[1]); c.attach(0); std::vector<char>b(size,'x'),out(size);
  for(size_t i=0;i<iters;i++){c.send(b.data(),size);c.recv(out.data(),size);if(out!=b)throw std::runtime_error("integrity failure");}
  int st; waitpid(pid,&st,0); c.teardown(0);
}

struct Options {
  std::string mech="pipe", mode="pingpong", pin="none", csv="results/raw.csv";
  size_t size=16, iters=0, warmup=0, run_id=0, timeout=60, spin_iters=2000;
  int cpu_a=-1, cpu_b=-1;
};
static uint64_t checksum(size_t seq, size_t size) {
  return 0x9e3779b97f4a7c15ULL ^ uint64_t(seq) ^ uint64_t(size);
}
static void fill(std::vector<uint8_t>& b, size_t seq) {
  uint64_t s=checksum(seq,b.size()); std::memcpy(b.data(),&s,8);
  std::memcpy(b.data()+8,&s,8); for(size_t i=16;i<b.size();++i)b[i]=uint8_t((i+seq)&255);
}
static bool valid(const std::vector<uint8_t>& b,size_t seq) {
  uint64_t s=0; std::memcpy(&s,b.data(),8); uint64_t t=checksum(seq,b.size());
  return s==t && std::memcmp(b.data()+8,&t,8)==0;
}
static void csv_row(const Options& o, const std::string& status, const std::vector<uint64_t>& samples,
                    double wall, const Usage& a, const Usage& b, bool chunked) {
  int fd=open(o.csv.c_str(),O_WRONLY|O_CREAT|O_APPEND,0644); if(fd<0) throw std::runtime_error("csv open");
  flock(fd,LOCK_EX);
  off_t end=lseek(fd,0,SEEK_END);
  if(end==0) { const char* h="timestamp,git_commit,mech,mode,size_bytes,iters,warmup,pin,run_id,chunked,status,mean_ns,p50_ns,p90_ns,p99_ns,p999_ns,min_ns,max_ns,stddev_ns,msgs_per_s,mb_per_s,wall_s,cpu_user_s,cpu_sys_s,cpu_pct,vol_ctx,invol_ctx,ctx_per_msg\n"; write_all(fd,h,std::strlen(h)); }
  double cpu_user=(a.user_us+b.user_us)/1e6, cpu_sys=(a.sys_us+b.sys_us)/1e6;
  double messages=double(o.iters), denom=wall>0?wall:1;
  std::ostringstream row; row<<std::time(nullptr)<<",-, "<<o.mech<<","<<o.mode<<","<<o.size<<","<<o.iters<<","<<o.warmup<<","<<o.pin<<","<<o.run_id<<","<<(chunked?"true":"false")<<","<<status<<",";
  if(samples.empty()) row<<",,,,,,,";
  else { row<<mean(samples)<<","<<percentile(samples,.50)<<","<<percentile(samples,.90)<<","<<percentile(samples,.99)<<","<<percentile(samples,.999)<<","<<*std::min_element(samples.begin(),samples.end())<<","<<*std::max_element(samples.begin(),samples.end())<<","<<stddev(samples); }
  row<<","<<(messages/denom)<<","<<(messages*o.size/denom/1048576.0)<<","<<wall<<","<<cpu_user<<","<<cpu_sys<<","<<((cpu_user+cpu_sys)/denom*100)<<","<<(a.vol+b.vol)<<","<<(a.invol+b.invol)<<","<<((a.vol+b.vol)/messages)<<"\n";
  std::string s=row.str(); write_all(fd,s.data(),s.size()); flock(fd,LOCK_UN); close(fd);
}

int run_benchmark(const Options& o) {
  auto cpus=allowed_cpus(); if(o.pin=="cross"&&cpus.size()<2) { std::cerr<<"skipped_cpus\n"; return 2; }
  int cpu_a=o.cpu_a>=0?o.cpu_a:(cpus.empty()?-1:cpus[0]);
  int cpu_b=o.cpu_b>=0?o.cpu_b:(cpus.size()>1?cpus[1]:cpu_a);
  auto c=make_channel(o.mech); c->setup(o.size); int ctl[2]; if(socketpair(AF_UNIX,SOCK_STREAM,0,ctl)) throw std::runtime_error("control socketpair");
  pid_t pid=fork(); if(pid<0) throw std::runtime_error("fork"); watched_pid=pid;
  signal(SIGALRM,alarm_handler); alarm(unsigned(o.timeout));
  if(!pid) {
    close(ctl[0]); c->attach(1); if(o.pin=="same"||o.pin=="cross") pin_cpu(o.pin=="same"?cpu_a:cpu_b);
    Usage before=usage(); std::vector<uint8_t>b(o.size); bool ok=true;
    for(size_t i=0;i<o.iters+o.warmup;i++){ c->recv(b.data(),b.size()); if(!valid(b,i))ok=false; if(o.mode=="pingpong") c->send(b.data(),b.size()); }
    if(o.mode=="stream"){char ack='a'; write_all(ctl[1],&ack,1);}
    Usage after=usage(); ChildReport report{delta(before,after),ok?1:0}; write_all(ctl[1],&report,sizeof(report)); c->teardown(1); _exit(ok?0:3);
  }
  close(ctl[1]); c->attach(0); if(o.pin=="same"||o.pin=="cross") pin_cpu(cpu_a);
  Usage before=usage(); std::vector<uint8_t>b(o.size),out(o.size); std::vector<uint64_t> samples;
  if(o.mode=="pingpong") samples.reserve(o.iters);
  size_t total=o.iters+o.warmup; bool ok=true; uint64_t start=now_ns();
  for(size_t i=0;i<total&&!timed_out;i++){fill(b,i);uint64_t t=now_ns();c->send(b.data(),b.size());if(o.mode=="pingpong"){c->recv(out.data(),out.size());if(!valid(out,i))ok=false;if(i>=o.warmup)samples.push_back(now_ns()-t);}}
  if(o.mode=="stream"&&!timed_out){ char ack; read_all(ctl[0],&ack,1); }
  uint64_t end=now_ns(); Usage after=usage(); ChildReport report{}; if(!timed_out) read_all(ctl[0],&report,sizeof(report));
  alarm(0); watched_pid=-1; int st=0; waitpid(pid,&st,0); c->teardown(0); close(ctl[0]);
  std::string status=timed_out?"timeout":(!ok||!report.ok?"integrity_error":"ok");
  bool is_chunked = c->chunked(o.size);
  csv_row(o,status,samples,(end-start)/1e9,delta(before,after),report.u,is_chunked);
  return status=="ok"?0:1;
}
