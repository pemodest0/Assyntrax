from __future__ import annotations

import math
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Tuple

import matplotlib.pyplot as plt
import numpy as np

from hypercube_walk import (
    aggregate_by_weight,
    classical_hypercube_time_series,
    grover_coin,
    hadamard_coin,
    hamming_weights,
    quantum_hypercube_time_series,
    quantum_hypercube_time_series_adaptive,
)
from plot_utils import plot_distribution_heatmap, plot_entropy_curves


def shannon_entropy(distribution: np.ndarray) -> float:
    mask = distribution > 0
    if not np.any(mask):
        return 0.0
    values = distribution[mask]
    return float(-np.sum(values * np.log2(values)))


def compute_weight_aggregate(series: np.ndarray, weights: np.ndarray) -> np.ndarray:
    aggregated = np.zeros((series.shape[0], weights.max() + 1), dtype=float)
    for idx, distribution in enumerate(series):
        aggregated[idx] = aggregate_by_weight(distribution, weights)
    return aggregated


def compute_weight_stats(aggregated: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    levels = np.arange(aggregated.shape[1], dtype=float)
    mean = aggregated @ levels
    variance = np.sum(aggregated * (levels - mean[:, None]) ** 2, axis=1)
    return mean, variance


def terrain_coin_callback(dimensions: int) -> Callable[[int, np.ndarray], np.ndarray]:
    indices = np.arange(1 << dimensions, dtype=np.int64)

    def callback(step: int, distribution: np.ndarray) -> np.ndarray:
        distribution = np.asarray(distribution, dtype=float)
        if distribution.shape != (indices.size,):
            raise ValueError("distribution has unexpected shape.")

        biases = []
        for axis in range(dimensions):
            bit_values = ((indices >> axis) & 1).astype(float)
            bias = float(np.dot(distribution, 1.0 - 2.0 * bit_values))
            biases.append(bias)

        vector = np.asarray(biases, dtype=np.complex128)
        norm = np.linalg.norm(vector)
        if norm < 1e-12:
            vector = np.ones(dimensions, dtype=np.complex128) / math.sqrt(dimensions)
        else:
            vector /= norm

        matrix = 2.0 * np.outer(vector, np.conjugate(vector)) - np.eye(dimensions, dtype=np.complex128)
        phase = np.exp(1j * 0.03 * step)
        return phase * matrix

    return callback


def plot_metric_vs_dimension(
    metrics: Dict[str, List[Tuple[int, float]]],
    ylabel: str,
    output_path: Path,
) -> None:
    fig, ax = plt.subplots(figsize=(8, 5))
    for label, series in metrics.items():
        dims = [item[0] for item in series]
        values = [item[1] for item in series]
        ax.plot(dims, values, marker="o", linewidth=2.0, label=label)
    ax.set_xlabel("Dimensão do hipercubo")
    ax.set_ylabel(ylabel)
    ax.grid(True, linestyle="--", alpha=0.3)
    ax.legend()
    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=300)
    plt.close(fig)


def generate_plots(dimensions: Iterable[int], steps: int = 60) -> None:
    output_root = Path("results_hypercube")
    output_root.mkdir(parents=True, exist_ok=True)

    entropy_metrics: Dict[str, List[Tuple[int, float]]] = {}
    variance_metrics: Dict[str, List[Tuple[int, float]]] = {}

    for dim in dimensions:
        weights = hamming_weights(dim)
        weight_levels = np.arange(dim + 1)
        dim_root = output_root / f"dimension_{dim}"
        dim_root.mkdir(parents=True, exist_ok=True)

        entropy_map: Dict[str, List[float]] = {}

        classical_series = classical_hypercube_time_series(dim, steps)
        classical_agg = compute_weight_aggregate(classical_series, weights)
        classical_entropy = [shannon_entropy(dist) for dist in classical_series]
        classical_mean, classical_var = compute_weight_stats(classical_agg)
        entropy_map[f"Clássico ({dim}D)"] = classical_entropy

        classical_dir = dim_root / "classical"
        classical_dir.mkdir(parents=True, exist_ok=True)
        plot_distribution_heatmap(
            classical_agg,
            weight_levels,
            f"Hipercubo {dim}D clássico",
            classical_dir / "distribution_heatmap.png",
        )

        entropy_metrics.setdefault("Clássico", []).append((dim, float(classical_entropy[-1])))
        variance_metrics.setdefault("Clássico", []).append((dim, float(classical_var[-1])))

        coins: List[Tuple[str, str, np.ndarray | Callable[[int, np.ndarray], np.ndarray]]] = [
            ("Grover", "grover", grover_coin(dim)),
        ]

        if dim & (dim - 1) == 0:
            coins.append(("Hadamard", "hadamard", hadamard_coin(dim)))

        coins.append(("Terreno adaptativo", "terrain", terrain_coin_callback(dim)))

        for label, slug, coin in coins:
            coin_dir = dim_root / slug
            coin_dir.mkdir(parents=True, exist_ok=True)

            if callable(coin):
                series = quantum_hypercube_time_series_adaptive(dim, steps, coin)  # type: ignore[arg-type]
            else:
                series = quantum_hypercube_time_series(dim, steps, coin_matrix=coin)  # type: ignore[arg-type]

            aggregated = compute_weight_aggregate(series, weights)
            entropies = [shannon_entropy(dist) for dist in series]
            mean_weight, variance_weight = compute_weight_stats(aggregated)

            entropy_map[f"{label} ({dim}D)"] = entropies

            plot_distribution_heatmap(
                aggregated,
                weight_levels,
                f"Hipercubo {dim}D – {label}",
                coin_dir / "distribution_heatmap.png",
            )

            metrics_label = f"{label}"
            entropy_metrics.setdefault(metrics_label, []).append((dim, float(entropies[-1])))
            variance_metrics.setdefault(metrics_label, []).append((dim, float(variance_weight[-1])))

        plot_entropy_curves(entropy_map, dim_root / "entropy_comparison.png")

    plot_metric_vs_dimension(
        entropy_metrics,
        "Entropia final (bits)",
        output_root / "entropy_vs_dimension.png",
    )
    plot_metric_vs_dimension(
        variance_metrics,
        "Variância final do peso de Hamming",
        output_root / "variance_vs_dimension.png",
    )


if __name__ == "__main__":
    generate_plots(dimensions=(4, 6, 8, 10), steps=60)
