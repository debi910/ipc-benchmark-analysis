#include "stats.h"
#include <algorithm>
#include <cmath>
#include <numeric>
double percentile(std::vector<uint64_t> v, double p) {
  if (v.empty()) return 0;
  std::sort(v.begin(), v.end());
  double x = p * (v.size() - 1);
  size_t i = size_t(x); double f = x - i;
  return i + 1 < v.size() ? v[i] * (1 - f) + v[i + 1] * f : v[i];
}
double mean(const std::vector<uint64_t>& v) {
  if (v.empty()) return 0;
  return std::accumulate(v.begin(), v.end(), 0.0) / v.size();
}
double stddev(const std::vector<uint64_t>& v) {
  if (v.size() < 2) return 0;
  double m = mean(v), s = 0; for (auto x : v) s += (x - m) * (x - m);
  return std::sqrt(s / (v.size() - 1));
}
