#include "channel.h"
#include <iostream>
void run_echo(Channel&,size_t,size_t);
int main(){for(const char*n:{"shm_futex","shm_hybrid"}){auto c=make_channel(n);run_echo(*c,65536,20);std::cout<<n<<": PASS\n";}}
