#include "channel.h"
#include <iostream>
void run_echo(Channel&,size_t,size_t);
int main(int argc,char**argv){if(argc==2&&std::string(argv[1])=="--list-mechs"){std::cout<<"pipe fifo mq uds shm_spin shm_futex shm_hybrid\n";return 0;}std::string mech="pipe";size_t size=16,iters=100;for(int i=1;i+1<argc;i++){std::string a=argv[i];if(a=="--mech")mech=argv[++i];else if(a=="--size")size=std::stoull(argv[++i]);else if(a=="--iters")iters=std::stoull(argv[++i]);}try{auto c=make_channel(mech);run_echo(*c,size,iters);std::cout<<"ok "<<mech<<" "<<size<<" "<<iters<<"\n";return 0;}catch(const std::exception&e){std::cerr<<e.what()<<"\n";return 1;}}
