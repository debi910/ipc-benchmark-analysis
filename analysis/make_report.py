#!/usr/bin/env python3
"""Generate compact figures and a measured summary from a benchmark CSV."""
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="results/raw.csv")
    parser.add_argument("--output", default="results")
    args = parser.parse_args()
    data = pd.read_csv(args.input, skipinitialspace=True)
    data.columns = data.columns.str.strip()
    data["mech"] = data["mech"].str.strip()
    data = data[data["status"].str.strip() == "ok"]
    output = Path(args.output)
    figures = output / "figures"
    figures.mkdir(parents=True, exist_ok=True)
    ping = data[data["mode"] == "pingpong"]
    stream = data[data["mode"] == "stream"]
    if not ping.empty:
        for column, name, ylabel in [("p50_ns", "latency_vs_size", "p50 RTT (ns)"),
                                     ("cpu_user_s", "cpu_cost_vs_size", "user CPU (s)")]:
            fig, ax = plt.subplots()
            for mech, group in ping.groupby("mech"):
                ax.plot(group["size_bytes"], group[column], marker="o", label=mech)
            ax.set_xscale("log"); ax.set_yscale("log"); ax.set_xlabel("message size (bytes)")
            ax.set_ylabel(ylabel); ax.legend(fontsize="small"); fig.tight_layout()
            fig.savefig(figures / f"{name}.png", dpi=150); plt.close(fig)
    if not stream.empty:
        fig, ax = plt.subplots()
        for mech, group in stream.groupby("mech"):
            ax.plot(group["size_bytes"], group["mb_per_s"], marker="o", label=mech)
        ax.set_xscale("log"); ax.set_xlabel("message size (bytes)"); ax.set_ylabel("MB/s")
        ax.legend(fontsize="small"); fig.tight_layout(); fig.savefig(figures / "throughput_vs_size.png", dpi=150)
        plt.close(fig)
    summary = data.groupby(["mech", "mode", "size_bytes"], as_index=False).median(numeric_only=True)
    summary.to_csv(output / "summary.csv", index=False)
    table = ["| " + " | ".join(summary.columns) + " |",
             "|" + "|".join("---" for _ in summary.columns) + "|"]
    table.extend("| " + " | ".join(str(value) for value in row) + " |"
                 for row in summary.itertuples(index=False, name=None))
    (output / "summary.md").write_text("# Measured summary\n\nGenerated from the supplied results CSV.\n\n"
                                      + "\n".join(table) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
