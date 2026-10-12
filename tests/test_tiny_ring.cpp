#include "channel.h"
#include <iostream>
void run_echo(Channel&, size_t, size_t);
int main() {
  for (const char* name : {"shm_spin", "shm_futex", "shm_hybrid"}) {
    auto channel = make_channel(name);
    run_echo(*channel, 65536, 20);
    std::cout << name << ": tiny 4KiB ring, 65536-byte messages x 20 PASS\n";
  }
}
