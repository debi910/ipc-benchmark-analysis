#include "channel.h"
#include <algorithm>
#include <iostream>
#include <string>
struct Options;
int run_benchmark(const Options&);
struct Options {
  std::string mech="pipe", mode="pingpong", pin="none", csv="results/raw.csv";
  size_t size=16, iters=0, warmup=0, run_id=0, timeout=60, spin_iters=2000;
  int cpu_a=-1, cpu_b=-1;
};
int main(int argc,char**argv) {
  Options o;
  if(argc==2&&std::string(argv[1])=="--list-mechs"){std::cout<<"pipe fifo mq uds shm_spin shm_futex shm_hybrid\n";return 0;}
  for(int i=1;i+1<argc;i++){std::string a=argv[i],v=argv[++i];
    if(a=="--mech")o.mech=v;else if(a=="--mode")o.mode=v;else if(a=="--size")o.size=std::stoull(v);
    else if(a=="--iters")o.iters=std::stoull(v);else if(a=="--warmup")o.warmup=std::stoull(v);
    else if(a=="--pin")o.pin=v;else if(a=="--run-id")o.run_id=std::stoull(v);else if(a=="--csv")o.csv=v;
    else if(a=="--timeout")o.timeout=std::stoull(v);else if(a=="--cpu-a")o.cpu_a=std::stoi(v);else if(a=="--cpu-b")o.cpu_b=std::stoi(v);
    else if(a=="--spin-iters")o.spin_iters=std::stoull(v);
  }
  if(!o.iters)o.iters=o.mode=="stream"?std::clamp<size_t>(268435456/o.size,2000,200000):(o.size<=65536?20000:2000);
  if(!o.warmup)o.warmup=o.iters/10;
  setenv("IPCB_SPIN_ITERS",std::to_string(o.spin_iters).c_str(),1);
  try{return run_benchmark(o);}catch(const std::exception&e){std::cerr<<e.what()<<"\n";return 1;}
}
