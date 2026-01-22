from __future__ import annotations

import math
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd


def build_series() -> pd.DataFrame:
    start = datetime(2025, 1, 1)
    points = 24 * 14
    times = [start + timedelta(hours=i) for i in range(points)]

    seasonal = [100 + 20 * math.sin(2 * math.pi * (i % 24) / 24) for i in range(points)]
    noise = np.random.normal(0, 5, size=points)
    values = np.array(seasonal) + noise

    # Inject a single anomaly.
    values[24 * 7] += 60

    return pd.DataFrame({"timestamp": times, "load": values})


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    output_csv = repo_root / "data" / "processed" / "synthetic_energy.csv"
    output_csv.parent.mkdir(parents=True, exist_ok=True)

    df = build_series()
    df.to_csv(output_csv, index=False)

    outdir = repo_root / "results" / "energy_demo"
    outdir.mkdir(parents=True, exist_ok=True)

    subprocess.run(
        [
            "python",
            "-m",
            "spa.run",
            "--input",
            str(output_csv),
            "--time-col",
            "timestamp",
            "--value-col",
            "load",
            "--outdir",
            str(outdir),
        ],
        check=True,
    )


if __name__ == "__main__":
    main()

