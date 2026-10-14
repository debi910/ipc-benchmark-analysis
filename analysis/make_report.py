#!/usr/bin/env python3
"""Generate figures, summaries, crossover analysis, and recommendation table."""
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

MECHANISMS = ["pipe", "fifo", "mq", "uds", "shm_spin", "shm_futex", "shm_hybrid"]
SHM = {"shm_spin", "shm_futex", "shm_hybrid"}


def load(path: str) -> pd.DataFrame:
    data = pd.read_csv(path, skipinitialspace=True)
    data.columns = data.columns.astype(str).str.strip()
    for column in data.select_dtypes(include=["object", "string"]).columns:
        data[column] = data[column].astype(str).str.strip()
    numeric = [c for c in data.columns if c not in {"git_commit", "mech", "mode", "pin", "status", "chunked"}]
    data[numeric] = data[numeric].apply(pd.to_numeric, errors="coerce")
    return data[data["status"] == "ok"].copy()


def median_rows(data: pd.DataFrame) -> pd.DataFrame:
    keys = ["mech", "mode", "pin", "size_bytes"]
    return data.groupby(keys, as_index=False).median(numeric_only=True)


def line_plot(frame: pd.DataFrame, x: str, y: str, ylabel: str, path: Path,
              title: str = "", log_y: bool = False) -> None:
    fig, ax = plt.subplots(figsize=(9, 5.5))
    for mech in MECHANISMS:
        group = frame[frame["mech"] == mech].sort_values(x)
        if group.empty:
            continue
        ax.plot(group[x], group[y], marker="o", linewidth=1.8, label=mech)
    ax.set_xscale("log")
    if log_y:
        ax.set_yscale("log")
    ax.set_xlabel("message size (bytes)")
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.grid(True, which="both", alpha=0.25)
    ax.legend(ncol=2, fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="results/raw.csv")
    parser.add_argument("--output", default="results")
    args = parser.parse_args()
    output = Path(args.output)
    figures = output / "figures"
    figures.mkdir(parents=True, exist_ok=True)
    data = load(args.input)
    med = median_rows(data)
    cross_ping = med[(med["mode"] == "pingpong") & (med["pin"] == "cross")]
    cross_stream = med[(med["mode"] == "stream") & (med["pin"] == "cross")]

    line_plot(cross_ping, "size_bytes", "p50_ns", "p50 RTT (ns)", figures / "latency_vs_size.png",
              "Cross-core ping-pong latency", log_y=True)
    line_plot(cross_stream, "size_bytes", "mb_per_s", "throughput (MB/s)", figures / "throughput_vs_size.png",
              "Cross-core stream throughput")
    cpu = cross_ping.copy()
    cpu["cpu_ns_per_msg"] = (cpu["cpu_user_s"] + cpu["cpu_sys_s"]) * 1e9 / cpu["iters"]
    line_plot(cpu, "size_bytes", "cpu_ns_per_msg", "CPU time per message (ns)",
              figures / "cpu_cost_vs_size.png", "Cross-core CPU cost", log_y=True)

    fig, ax = plt.subplots(figsize=(10, 6))
    for mech in MECHANISMS:
        group = cross_ping[cross_ping["mech"] == mech].copy()
        group["cpu_ns_per_msg"] = (group["cpu_user_s"] + group["cpu_sys_s"]) * 1e9 / group["iters"]
        ax.plot(group["p50_ns"], group["cpu_ns_per_msg"], marker="o", linewidth=1.5,
                label=mech)
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlabel("p50 RTT (ns)"); ax.set_ylabel("CPU time per message (ns)")
    ax.set_title("Latency–CPU trade-off, cross-core ping-pong")
    ax.grid(True, which="both", alpha=0.25); ax.legend(ncol=2, fontsize=8)
    fig.tight_layout(); fig.savefig(figures / "latency_vs_cpu_tradeoff.png", dpi=150); plt.close(fig)

    tail = cross_ping.copy()
    tail["tail_ratio"] = tail["p99_ns"] / tail["p50_ns"]
    fig, ax = plt.subplots(figsize=(10, 5.5))
    for mech in MECHANISMS:
        group = tail[tail["mech"] == mech].sort_values("size_bytes")
        ax.plot(group["size_bytes"], group["tail_ratio"], marker="o", label=mech)
    ax.set_xscale("log"); ax.set_xlabel("message size (bytes)"); ax.set_ylabel("p99 / p50")
    ax.set_title("Tail-latency amplification"); ax.grid(True, which="both", alpha=0.25)
    ax.legend(ncol=2, fontsize=8); fig.tight_layout()
    fig.savefig(figures / "tail_ratio.png", dpi=150); plt.close(fig)

    ctx = cross_ping.copy()
    fig, ax = plt.subplots(figsize=(9, 5.5))
    for mech in MECHANISMS:
        group = ctx[ctx["mech"] == mech].sort_values("size_bytes")
        ax.plot(group["size_bytes"], group["ctx_per_msg"], marker="o", label=mech)
    ax.set_xscale("log"); ax.set_xlabel("message size (bytes)"); ax.set_ylabel("context switches / message")
    ax.set_title("Context-switch cost"); ax.grid(True, which="both", alpha=0.25)
    ax.legend(ncol=2, fontsize=8); fig.tight_layout()
    fig.savefig(figures / "ctx_switches_per_msg.png", dpi=150); plt.close(fig)

    pin = med[(med["mode"] == "pingpong") & (med["size_bytes"].isin([16, 4096, 65536]))]
    fig, axes = plt.subplots(1, 3, figsize=(13, 4.8), sharey=False)
    for ax, size in zip(axes, [16, 4096, 65536]):
        subset = pin[pin["size_bytes"] == size]
        for mech in MECHANISMS:
            vals = subset[subset["mech"] == mech].set_index("pin")
            if {"cross", "same"} <= set(vals.index):
                ax.plot(["cross", "same"], [vals.loc["cross", "p50_ns"], vals.loc["same", "p50_ns"]],
                        marker="o", label=mech)
        ax.set_title(f"{size} bytes"); ax.set_yscale("log"); ax.grid(True, alpha=0.25)
        ax.set_ylabel("p50 RTT (ns)"); ax.set_xlabel("pinning")
    axes[0].legend(fontsize=7, ncol=2); fig.suptitle("Pinning effect on ping-pong latency")
    fig.tight_layout(); fig.savefig(figures / "pinning_effect.png", dpi=150); plt.close(fig)

    med.to_csv(output / "summary.csv", index=False)
    lines = ["# Measured summary", "", "All values are medians over repetitions; source: `results/raw.csv`.", ""]
    for size in sorted(cross_ping["size_bytes"].unique()):
        lines += [f"## Cross-core ping-pong at {int(size)} bytes", "",
                  "| Mechanism | p50 RTT (ns) | p99 RTT (ns) | CPU/msg (ns) | ctx/msg |",
                  "|---|---:|---:|---:|---:|"]
        rows = cross_ping[cross_ping["size_bytes"] == size].copy()
        rows["cpu_ns"] = (rows["cpu_user_s"] + rows["cpu_sys_s"]) * 1e9 / rows["iters"]
        for _, row in rows.sort_values("p50_ns").iterrows():
            lines.append(f"| {row.mech} | {row.p50_ns:.1f} | {row.p99_ns:.1f} | {row.cpu_ns:.1f} | {row.ctx_per_msg:.3f} |")
        lines.append("")
    lines += ["## Crossover analysis", "",
              "Smallest measured stream size where a shared-memory variant reaches at least 20% more throughput than both pipe and UDS:"]
    for mech in sorted(SHM):
        found = []
        for size in sorted(cross_stream["size_bytes"].unique()):
            row = cross_stream[(cross_stream.mech == mech) & (cross_stream.size_bytes == size)]
            pipe = cross_stream[(cross_stream.mech == "pipe") & (cross_stream.size_bytes == size)]
            uds = cross_stream[(cross_stream.mech == "uds") & (cross_stream.size_bytes == size)]
            if not row.empty and not pipe.empty and not uds.empty:
                value = row.iloc[0].mb_per_s
                pipe_value = pipe.iloc[0].mb_per_s
                uds_value = uds.iloc[0].mb_per_s
            else:
                value = pipe_value = uds_value = 0
            if not row.empty and not pipe.empty and not uds.empty and value >= 1.2 * pipe_value and value >= 1.2 * uds_value:
                found.append(int(size))
        lines.append(f"- `{mech}`: {min(found) if found else 'none found'}")
    lines.append("")
    (output / "summary.md").write_text("\n".join(lines) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
