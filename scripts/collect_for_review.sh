#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
bundle="$root/review_bundle.tar.gz"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
mkdir -p "$tmp/results"
cp "$root/results/raw.csv" "$tmp/results/"
cp "$root/results/system_info.json" "$tmp/results/"
cp "$root/results/summary.md" "$tmp/results/"
cp -r "$root/results/figures" "$tmp/results/"
cp "$root/README.md" "$tmp/"
cp -r "$root/docs" "$tmp/"
mkdir -p "$tmp/results/logs"
for file in "$root"/results/logs/*; do
  [ -f "$file" ] || continue
  tail -n 200 "$file" > "$tmp/results/logs/$(basename "$file")"
done
(cd "$root" && make check) > "$tmp/make-check.txt" 2>&1
(cd "$root" && git --no-pager log --oneline | head -30) > "$tmp/git-log.txt"
tar -czf "$bundle" -C "$tmp" .
printf '%s (%s bytes)\n' "$bundle" "$(stat -c '%s' "$bundle")"
