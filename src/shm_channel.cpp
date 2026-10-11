#include "channel.h"
#include "shm_ring.h"
#include <sys/mman.h>
#include <fcntl.h>
#include <stdexcept>
#include <cstring>
class ShmChannel final : public Channel {
 ShmRing* rings[2]{nullptr,nullptr}; int role=0; std::string mode;
 void transfer(void* out,const void* in,size_t n,bool writing) {
  ShmRing* r=rings[writing?role:1-role]; uint8_t* dst=(uint8_t*)out; const uint8_t* src=(const uint8_t*)in;
  while(n){ uint64_t h=r->head.load(std::memory_order_acquire),t=r->tail.load(std::memory_order_acquire); uint64_t avail=writing?sizeof(r->data)-(h-t):h-t; if(!avail){ if(mode=="spin"){cpu_relax();continue;} uint32_t* seq=writing?reinterpret_cast<uint32_t*>(&r->space_seq):reinterpret_cast<uint32_t*>(&r->data_seq); r->producer_waiting.store(writing, std::memory_order_seq_cst); uint32_t s=*seq; if((writing?r->head.load():r->head.load())-(writing?r->tail.load():r->tail.load())==(writing?sizeof(r->data):0)){futex_wait(reinterpret_cast<std::atomic<uint32_t>*>(seq),s);} continue;} size_t k=std::min<uint64_t>(n,avail); size_t at=(writing?h:t)%sizeof(r->data); size_t first=std::min(k,sizeof(r->data)-at); if(writing){memcpy(r->data+at,src,first);if(first<k)memcpy(r->data,src+first,k-first);r->head.store(h+k,std::memory_order_release);r->data_seq.fetch_add(1);futex_wake(&r->data_seq);src+=k;}else{memcpy(dst,r->data+at,first);if(first<k)memcpy(dst+first,r->data,k-first);r->tail.store(t+k,std::memory_order_release);r->space_seq.fetch_add(1);futex_wake(&r->space_seq);dst+=k;}n-=k; }
 }
 public:
 explicit ShmChannel(std::string m):mode(std::move(m)){}
 void setup(size_t)override{for(auto& r:rings){void*p=mmap(nullptr,sizeof(ShmRing),PROT_READ|PROT_WRITE,MAP_SHARED|MAP_ANONYMOUS,-1,0);if(p==MAP_FAILED)throw std::runtime_error("mmap");r=new(p)ShmRing;}}
 void attach(int r)override{role=r;}
 void send(const void*p,size_t n)override{transfer(nullptr,p,n,true);}
 void recv(void*p,size_t n)override{transfer(p,nullptr,n,false);}
 void teardown(int)override{for(auto&r:rings)if(r){munmap(r,sizeof(ShmRing));r=nullptr;}}
 const char*name()const override{return mode.c_str();}
};
std::unique_ptr<Channel> make_shm(const std::string& n){return std::make_unique<ShmChannel>(n);}
