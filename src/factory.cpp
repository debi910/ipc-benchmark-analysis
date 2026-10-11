#include "channel.h"
#include <stdexcept>
std::unique_ptr<Channel> make_pipe(); std::unique_ptr<Channel> make_fifo(); std::unique_ptr<Channel> make_mq(); std::unique_ptr<Channel> make_uds(); std::unique_ptr<Channel> make_shm(const std::string&);
std::unique_ptr<Channel> make_channel(const std::string& n){if(n=="pipe")return make_pipe();if(n=="fifo")return make_fifo();if(n=="mq")return make_mq();if(n=="uds")return make_uds();if(n=="shm_spin"||n=="shm_futex"||n=="shm_hybrid")return make_shm(n);throw std::invalid_argument("unknown channel: "+n);}
