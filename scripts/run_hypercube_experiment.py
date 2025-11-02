from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, Tuple

import numpy as np
import pandas as pd

from hypercube_walk import (
    aggregate_by_weight,
    classical_hypercube_time_series,
    hamming_weights,
    quantum_hypercube_time_series,
)


def grover_coin(dimension: int) -> np.ndarray:
    """Return Grover diffusion coin matrix for the given dimension."""
    identity = np.eye(dimension, dtype=np.complex128)
    ones = np.ones((dimension, dimension), dtype=np.complex128)
    return (2.0 / dimension) * ones - identity


def shannon_entropy(distribution: np.ndarray, base: float = 2.0) -> float:
    """Compute Shannon entropy for a probability distribution."""
    mask = distribution > 0
    if not np.any(mask):
        return 0.0
    log_base = math.log(base)
    return float(-np.sum(distribution[mask] * (np.log(distribution[mask]) / log_base)))


def aggregate_stats(
    distribution: np.ndarray,
    weights: np.ndarray,
) -> Tuple[float, float]:
    """Return mean weight and variance for the distribution."""
    mean = float(np.dot(distribution, weights))
    variance = float(np.dot(distribution, (weights - mean) ** 2))
    return mean, variance


def diffusion_alpha(variance_series: np.ndarray) -> float:
    """Estimate diffusion exponent alpha via log-log fit of variance vs time."""
    steps = np.arange(variance_series.size, dtype=float)
    mask = (steps >= 1) & (variance_series > 0)
    if np.count_nonzero(mask) < 2:
        return float("nan")
    log_t = np.log(steps[mask])
    log_var = np.log(variance_series[mask])
    slope, _ = np.polyfit(log_t, log_var, 1)
    return float(slope)


def run_mode(
    distributions: np.ndarray,
    weights: np.ndarray,
    label: str,
) -> Dict[str, Iterable[float]]:
    steps = np.arange(distributions.shape[0], dtype=int)
    entropies = np.array([shannon_entropy(dist) for dist in distributions], dtype=float)
    means = np.zeros_like(entropies)
    variances = np.zeros_like(entropies)
    aggregated = np.array(
        [aggregate_by_weight(dist, weights) for dist in distributions],
        dtype=float,
    )
    for idx, dist in enumerate(distributions):
        mean, variance = aggregate_stats(dist, weights)
        means[idx] = mean
        variances[idx] = variance

    data = {
        "step": steps,
        "entropy": entropies,
        "mean_weight": means,
        "variance_weight": variances,
        "alpha_running": np.concatenate([[np.nan], np.diff(means)]),
    }
    for weight_idx in range(aggregated.shape[1]):
        data[f"weight_{weight_idx}"] = aggregated[:, weight_idx]
    df = pd.DataFrame(data)
    return {
        "label": label,
        "dataframe": df,
        "entropy_final": float(entropies[-1]),
        "entropy_mean": float(entropies.mean()),
        "variance_final": float(variances[-1]),
        "alpha_estimate": diffusion_alpha(variances),
    }


@dataclass
class ExperimentConfig:
    dimensions: Tuple[int, ...] = (4, 6, 8, 10)
    steps: int = 60


def run_experiment(config: ExperimentConfig) -> None:
    output_root = Path("hypercube_results")
    output_root.mkdir(parents=True, exist_ok=True)

    summary_rows = []

    for dim in config.dimensions:
        print(f"[INFO] Running hypercube experiment for dimension {dim} ({config.steps} steps)")
        weights = hamming_weights(dim)

        classical_series = classical_hypercube_time_series(dim, config.steps)
        quantum_series = quantum_hypercube_time_series(dim, config.steps, coin_matrix=grover_coin(dim))

        results = []
        results.append(run_mode(classical_series, weights, label="classical"))
        results.append(run_mode(quantum_series, weights, label="quantum_grover"))

        dim_dir = output_root / f"dimension_{dim}"
        dim_dir.mkdir(parents=True, exist_ok=True)

        for result in results:
            df = result["dataframe"]
            csv_path = dim_dir / f"{result['label']}_timeseries.csv"
            df.to_csv(csv_path, index=False)

            summary_rows.append(
                {
                    "dimension": dim,
                    "mode": result["label"],
                    "entropy_final": result["entropy_final"],
                    "entropy_mean": result["entropy_mean"],
                    "variance_final": result["variance_final"],
                    "alpha_estimate": result["alpha_estimate"],
                }
            )

    summary_df = pd.DataFrame(summary_rows)
    summary_path = output_root / "experiment_summary.csv"
    summary_df.to_csv(summary_path, index=False)
    print(f"[INFO] Summary saved to {summary_path}")


def main() -> None:
    config = ExperimentConfig()
    run_experiment(config)


if __name__ == "__main__":
    main()
