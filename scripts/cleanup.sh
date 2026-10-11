#!/usr/bin/env bash
set -euo pipefail

remove_prefix() {
  local dir="$1" prefix="$2"
  [ -d "$dir" ] || return 0
  find "$dir" -maxdepth 1 -mindepth 1 -name "${prefix}*" -type f -delete 2>/dev/null || true
}

remove_prefix "/tmp" "ipcbench_fifo_"
remove_prefix "/dev/shm" "ipcbench_"
remove_prefix "/dev/mqueue" "ipcbench_mq_"
