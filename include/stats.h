#pragma once
#include <vector>
#include <cstdint>
double percentile(std::vector<uint64_t> values, double p);
double mean(const std::vector<uint64_t>& values);
double stddev(const std::vector<uint64_t>& values);
