#include "stats.h"
#include <cassert>
#include <iostream>
int main(){std::vector<uint64_t>v{1,2,3,4,5};assert(percentile(v,.5)==3);assert(percentile(v,.9)==4.6);assert(mean(v)==3);std::cout<<"test_stats: PASS\n";}
