#include "channel.h"
#include <cassert>
#include <iostream>
void run_echo(Channel&,size_t,size_t);
int main(){for(const char*n:{"pipe","fifo","mq","uds","shm_spin","shm_futex","shm_hybrid"}){auto c=make_channel(n);run_echo(*c,16,20);run_echo(*c,4096,5);std::cout<<n<<": PASS\n";}}
