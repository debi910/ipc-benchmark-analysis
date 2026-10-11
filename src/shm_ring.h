#pragma once
#include "timing.h"
#include "sysutil.h"
#include <atomic>
#include <sys/mman.h>
#include <linux/futex.h>
#include <sys/syscall.h>
#include <unistd.h>
#include <cerrno>
struct ShmRing { std::atomic<uint64_t> head{0},tail{0}; std::atomic<uint32_t> data_seq{0},space_seq{0}; std::atomic<uint32_t> consumer_waiting{0},producer_waiting{0}; uint8_t data[262144]; };
inline int futex_wait(std::atomic<uint32_t>* p,uint32_t v){return syscall(SYS_futex,reinterpret_cast<uint32_t*>(p),FUTEX_WAIT,v,nullptr,nullptr,0);}
inline void futex_wake(std::atomic<uint32_t>* p){syscall(SYS_futex,reinterpret_cast<uint32_t*>(p),FUTEX_WAKE,1,nullptr,nullptr,0);}
