#!/usr/bin/env bash
set -eu
root="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
bin="$root/build/ipcbench"
tmp="$(mktemp)"
trap 'rm -f "$tmp"' EXIT
printf 'mechanism,wall_s,status\n'
for mech in pipe shm_futex shm_spin; do
  before=$(date +%s%N)
  if timeout 15 "$bin" --mech "$mech" --mode pingpong --size 16 --iters 5000 --warmup 500 --pin cross --csv "$tmp" >/dev/null 2>&1; then status=ok; else status=timeout; fi
  after=$(date +%s%N)
  awk -v m="$mech" -v s="$status" -v w="$((after-before))" 'BEGIN { printf "%s,%.3f,%s\n", m, w/1000000000, s }'
done
