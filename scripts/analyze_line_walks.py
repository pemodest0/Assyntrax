from __future__ import annotations

import math
from pathlib import Path
from typing import Dict, Tuple
import sys

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from classical_walk import classical_random_walk_time_series
from quantum_walk import balanced_rotation_coin, hadamard_coin, quantum_random_walk_time_series

MAX_STEPS = 200
TARGET_POSITION = 50
SELECTED_STEPS = (10, 20, 50, 100, 200)
TAIL_THRESHOLD = 30
NORMALIZATION_TOL = 1e-12
SYMMETRY_TOL = 1e-9
VARIANCE_TOL = 2e-2
FIT_RANGE = (20, MAX_STEPS)
DECOHERENCE_P_VALUES = np.linspace(0.0, 1.0, 11)

RESULTS_DIR = ROOT / "outputs" / "1d_walks" / "line_analysis"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

HADAMARD_COIN = hadamard_coin()
HADAMARD_INITIAL = (1.0 / math.sqrt(2.0), 1.0j / math.sqrt(2.0))

ROTATION_COIN = balanced_rotation_coin(math.pi / 4)
ROTATION_INITIAL = HADAMARD_INITIAL

MODEL_LABELS: Dict[str, str] = {
    "classical": "Classical random walk",
    "hadamard": "Quantum walk (Hadamard coin)",
    "rotation": "Quantum walk (R(π/4) coin)",
}

COLORS: Dict[str, str] = {
    "classical": "black",
    "hadamard": "#6A0DAD",
    "rotation": "#ff7f0e",
}

MODEL_ORDER = ("classical", "hadamard", "rotation")


def ensure_normalization(series: np.ndarray, tol: float = NORMALIZATION_TOL) -> None:
    sums = series.sum(axis=1)
    max_dev = float(np.max(np.abs(sums - 1.0)))
    if max_dev > tol:
        raise ValueError(f"Probability normalization failed (max deviation={max_dev:.2e})")


def ensure_symmetry(series: np.ndarray, tol: float = SYMMETRY_TOL) -> None:
    max_dev = 0.0
    for step in range(series.shape[0]):
        probs = series[step]
        deviation = float(np.max(np.abs(probs - probs[::-1])))
        max_dev = max(max_dev, deviation)
    if max_dev > tol:
        raise ValueError(f"Hadamard walk lost symmetry (max asymmetry={max_dev:.2e})")


def _half_span(series: np.ndarray) -> int:
    return (series.shape[1] - 1) // 2


def _distribution_for_step(series: np.ndarray, step: int) -> np.ndarray:
    span = _half_span(series)
    start = span - step
    end = span + step + 1
    return series[step, start:end]


def validate_classical_moments(series: np.ndarray, variance_tolerance: float = VARIANCE_TOL) -> None:
    for step in range(1, series.shape[0]):
        probs = _distribution_for_step(series, step)
        positions = np.arange(-step, step + 1)
        mean = float(np.dot(positions, probs))
        variance = float(np.dot((positions - mean) ** 2, probs))
        if abs(mean) > 1e-10:
            raise ValueError(f"Classical walk mean deviates from zero at step {step} (mean={mean:.2e})")
        if abs(variance - step) > variance_tolerance * max(1.0, step):
            raise ValueError(
                f"Classical walk variance deviates from t at step {step} "
                f"(variance={variance:.4f}, expected≈{step})"
            )


def entropy_bits(probabilities: np.ndarray) -> float:
    nonzero = probabilities[probabilities > 0]
    if nonzero.size == 0:
        return 0.0
    return float(-np.sum(nonzero * np.log2(nonzero)))


def compute_moments(probabilities: np.ndarray, positions: np.ndarray) -> Tuple[float, float, float, float]:
    mean = float(np.dot(positions, probabilities))
    variance = float(np.dot((positions - mean) ** 2, probabilities))
    std_dev = math.sqrt(max(variance, 0.0))
    entropy = entropy_bits(probabilities)
    return mean, variance, std_dev, entropy


def tail_probability(probabilities: np.ndarray, positions: np.ndarray, threshold: int) -> float:
    mask = np.abs(positions) > threshold
    return float(np.sum(probabilities[mask]))


def compute_dispersion_curve(series: np.ndarray) -> np.ndarray:
    sigmas = np.zeros(series.shape[0], dtype=float)
    for step in range(series.shape[0]):
        positions = np.arange(-step, step + 1)
        probs = _distribution_for_step(series, step)
        _, variance, std_dev, _ = compute_moments(probs, positions)
        sigmas[step] = std_dev
    return sigmas


def fit_scaling_exponent(sigma: np.ndarray, fit_min: int, fit_max: int) -> Tuple[float, float]:
    steps = np.arange(sigma.size)
    mask = (steps >= fit_min) & (steps <= fit_max) & (sigma > 0.0)
    if mask.sum() < 2:
        return float("nan"), float("nan")
    x = np.log(steps[mask])
    y = np.log(sigma[mask])
    slope, intercept = np.polyfit(x, y, 1)
    return float(slope), float(intercept)


def plot_dispersion_loglog(
    curves: Dict[str, np.ndarray],
    output_path: Path,
    fit_range: Tuple[int, int],
) -> Dict[str, float]:
    steps = np.arange(MAX_STEPS + 1)
    fig, ax = plt.subplots(figsize=(10, 6))
    slopes: Dict[str, float] = {}

    for key in MODEL_ORDER:
        sigma = curves[key]
        valid = (steps > 0) & (sigma > 0.0)
        ax.loglog(steps[valid], sigma[valid], label=MODEL_LABELS[key], color=COLORS[key], linewidth=2.2)

        slope, intercept = fit_scaling_exponent(sigma, *fit_range)
        slopes[key] = slope
        if not math.isnan(slope):
            xfit = np.linspace(fit_range[0], fit_range[1], 200)
            yfit = np.exp(intercept) * xfit ** slope
            ax.loglog(xfit, yfit, linestyle="--", color=COLORS[key], alpha=0.5)
            ax.text(
                xfit[-1],
                yfit[-1],
                f"α={slope:.3f}",
                color=COLORS[key],
                fontsize=10,
                ha="right",
                va="bottom",
            )

    ax.set_xlabel("Steps (log scale)")
    ax.set_ylabel("σ(t) (log scale)")
    ax.set_title("Dispersion scaling σ(t) ∝ t^α")
    ax.grid(True, which="both", linestyle="--", alpha=0.3)
    ax.legend(loc="upper left")

    fig.tight_layout()
    fig.savefig(output_path, dpi=300)
    plt.close(fig)
    print(f"Saved {output_path}")
    return slopes


def plot_distributions_at_step(
    series: Dict[str, np.ndarray],
    step: int,
    output_path: Path,
) -> None:
    positions = np.arange(-step, step + 1)
    fig, ax = plt.subplots(figsize=(10, 6))

    for key in MODEL_ORDER:
        probs = _distribution_for_step(series[key], step)
        linestyle = "-" if key != "rotation" else "--"
        ax.plot(
            positions,
            probs,
            label=MODEL_LABELS[key],
            color=COLORS[key],
            linewidth=2.2,
            linestyle=linestyle,
        )

    ax.set_xlabel("Position")
    ax.set_ylabel("Probability")
    ax.set_title(f"Probability distributions at step {step}")
    ax.legend()
    ax.grid(True, linestyle="--", alpha=0.3)

    fig.tight_layout()
    fig.savefig(output_path, dpi=300)
    plt.close(fig)
    print(f"Saved {output_path}")


def classical_first_hit_distribution(n_steps: int, target: int) -> np.ndarray:
    size = 2 * n_steps + 1
    origin = n_steps
    target_index = origin + target

    current = np.zeros(size, dtype=float)
    current[origin] = 1.0
    hits = np.zeros(n_steps + 1, dtype=float)

    for step in range(1, n_steps + 1):
        updated = np.zeros_like(current)
        updated[1:] += 0.5 * current[:-1]
        updated[:-1] += 0.5 * current[1:]

        hit_prob = updated[target_index]
        hits[step] = hit_prob
        updated[target_index] = 0.0
        current = updated

    return hits


def _apply_coin(psi0: np.ndarray, psi1: np.ndarray, coin_matrix: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    c00, c01 = coin_matrix[0, 0], coin_matrix[0, 1]
    c10, c11 = coin_matrix[1, 0], coin_matrix[1, 1]
    new_psi0 = c00 * psi0 + c01 * psi1
    new_psi1 = c10 * psi0 + c11 * psi1
    return new_psi0, new_psi1


def quantum_first_hit_distribution(
    n_steps: int,
    target: int,
    coin_matrix: np.ndarray,
    coin_state: Tuple[complex, complex],
) -> np.ndarray:
    size = 2 * n_steps + 1
    origin = n_steps
    target_index = origin + target

    psi0 = np.zeros(size, dtype=np.complex128)
    psi1 = np.zeros(size, dtype=np.complex128)
    psi0[origin] = coin_state[0]
    psi1[origin] = coin_state[1]

    hits = np.zeros(n_steps + 1, dtype=float)

    for step in range(1, n_steps + 1):
        psi0_coin, psi1_coin = _apply_coin(psi0, psi1, coin_matrix)

        shifted_psi0 = np.zeros_like(psi0)
        shifted_psi1 = np.zeros_like(psi1)
        shifted_psi0[:-1] = psi0_coin[1:]
        shifted_psi1[1:] = psi1_coin[:-1]

        psi0, psi1 = shifted_psi0, shifted_psi1

        hit_prob = float((np.abs(psi0[target_index]) ** 2 + np.abs(psi1[target_index]) ** 2).real)
        hits[step] = hit_prob

        psi0[target_index] = 0.0
        psi1[target_index] = 0.0

    return hits


def plot_first_hit_distributions(
    hits: Dict[str, np.ndarray],
    output_path: Path,
) -> None:
    steps = np.arange(MAX_STEPS + 1)
    fig, axes = plt.subplots(1, 2, figsize=(14, 5), sharex=True)

    for key in MODEL_ORDER:
        axes[0].plot(steps, hits[key], label=MODEL_LABELS[key], color=COLORS[key], linewidth=2.0)
        axes[1].plot(
            steps,
            np.cumsum(hits[key]),
            label=MODEL_LABELS[key],
            color=COLORS[key],
            linewidth=2.0,
        )

    axes[0].set_title(f"First-hit probability at target +{TARGET_POSITION}")
    axes[0].set_xlabel("Steps")
    axes[0].set_ylabel("Probability of first detection")
    axes[0].grid(True, linestyle="--", alpha=0.3)

    axes[1].set_title("Cumulative detection probability")
    axes[1].set_xlabel("Steps")
    axes[1].set_ylabel("Cumulative probability")
    axes[1].grid(True, linestyle="--", alpha=0.3)
    axes[1].legend(loc="lower right")

    fig.suptitle("First-hit statistics for walks aiming at position +50")
    fig.tight_layout()
    fig.savefig(output_path, dpi=300)
    plt.close(fig)
    print(f"Saved {output_path}")


def plot_hadamard_heatmap(series: np.ndarray, output_path: Path) -> None:
    positions = np.arange(-MAX_STEPS, MAX_STEPS + 1)
    extent = (positions[0] - 0.5, positions[-1] + 0.5, 0, MAX_STEPS)

    fig, ax = plt.subplots(figsize=(12, 6))
    im = ax.imshow(
        series,
        origin="lower",
        aspect="auto",
        extent=extent,
        cmap="magma",
        vmin=0.0,
        vmax=series.max(),
    )
    ax.set_xlabel("Position")
    ax.set_ylabel("Steps")
    ax.set_title("Hadamard walk probability density (position × time)")

    cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label("Probability")

    fig.tight_layout()
    fig.savefig(output_path, dpi=300)
    plt.close(fig)
    print(f"Saved {output_path}")


def save_metrics_table(series: Dict[str, np.ndarray], output_path: Path) -> None:
    rows = []
    for key in MODEL_ORDER:
        probs_series = series[key]
        for step in SELECTED_STEPS:
            distribution = _distribution_for_step(probs_series, step)
            positions = np.arange(-step, step + 1)
            mean, variance, std_dev, entropy = compute_moments(distribution, positions)
            tail_prob = tail_probability(distribution, positions, TAIL_THRESHOLD)
            rows.append(
                {
                    "model": MODEL_LABELS[key],
                    "step": step,
                    "mean": mean,
                    "variance": variance,
                    "std_dev": std_dev,
                    "entropy_bits": entropy,
                    f"tail_prob_|x|>{TAIL_THRESHOLD}": tail_prob,
                }
            )

    df = pd.DataFrame(rows)
    df.to_csv(output_path, index=False)
    print(f"Saved {output_path}")


def save_first_hit_table(hits: Dict[str, np.ndarray], output_path: Path) -> None:
    rows = []
    steps = np.arange(MAX_STEPS + 1)
    for key in MODEL_ORDER:
        distribution = hits[key]
        cumulative = np.cumsum(distribution)
        for step, prob, cumulative_prob in zip(steps, distribution, cumulative):
            rows.append(
                {
                    "model": MODEL_LABELS[key],
                    "step": step,
                    "first_hit_probability": prob,
                    "cumulative_probability": cumulative_prob,
                }
            )
    df = pd.DataFrame(rows)
    df.to_csv(output_path, index=False)
    print(f"Saved {output_path}")


def run_decoherence_analysis(
    hadamard_series: np.ndarray,
    classical_series: np.ndarray,
    fit_range: Tuple[int, int],
    output_csv: Path,
    output_fig: Path,
) -> None:
    records = []
    exponents = []

    for p in DECOHERENCE_P_VALUES:
        mixed = (1.0 - p) * hadamard_series + p * classical_series
        normalization = mixed.sum(axis=1, keepdims=True)
        normalization[normalization == 0.0] = 1.0
        mixed = mixed / normalization
        sigma = compute_dispersion_curve(mixed)
        slope, _ = fit_scaling_exponent(sigma, *fit_range)
        records.append({"p": p, "scaling_exponent": slope})
        exponents.append(slope)

    df = pd.DataFrame(records)
    df.to_csv(output_csv, index=False)
    print(f"Saved {output_csv}")

    fig, ax = plt.subplots(figsize=(7, 5))
    ax.plot(DECOHERENCE_P_VALUES, exponents, marker="o", color="#6A0DAD", linewidth=2.0)
    ax.set_xlabel("Decoherence probability p")
    ax.set_ylabel("Scaling exponent α (σ(t) ∝ t^α)")
    ax.set_title("Dispersion exponent under decoherence mixing")
    ax.grid(True, linestyle="--", alpha=0.3)
    fig.tight_layout()
    fig.savefig(output_fig, dpi=300)
    plt.close(fig)
    print(f"Saved {output_fig}")


def main() -> None:
    classical_series = classical_random_walk_time_series(MAX_STEPS)
    hadamard_series = quantum_random_walk_time_series(
        MAX_STEPS,
        coin_matrix=HADAMARD_COIN,
        coin_state=HADAMARD_INITIAL,
    )
    rotation_series = quantum_random_walk_time_series(
        MAX_STEPS,
        coin_matrix=ROTATION_COIN,
        coin_state=ROTATION_INITIAL,
    )

    ensure_normalization(classical_series)
    ensure_normalization(hadamard_series)
    ensure_normalization(rotation_series)

    ensure_symmetry(hadamard_series)
    validate_classical_moments(classical_series)

    series_dict = {
        "classical": classical_series,
        "hadamard": hadamard_series,
        "rotation": rotation_series,
    }

    dispersion_curves = {key: compute_dispersion_curve(series) for key, series in series_dict.items()}
    plot_dispersion_loglog(dispersion_curves, RESULTS_DIR / "dispersion_loglog.png", FIT_RANGE)

    plot_distributions_at_step(series_dict, 100, RESULTS_DIR / "distributions_step100.png")

    classical_hits = classical_first_hit_distribution(MAX_STEPS, TARGET_POSITION)
    hadamard_hits = quantum_first_hit_distribution(MAX_STEPS, TARGET_POSITION, HADAMARD_COIN, HADAMARD_INITIAL)
    rotation_hits = quantum_first_hit_distribution(MAX_STEPS, TARGET_POSITION, ROTATION_COIN, ROTATION_INITIAL)

    hits_dict = {
        "classical": classical_hits,
        "hadamard": hadamard_hits,
        "rotation": rotation_hits,
    }
    plot_first_hit_distributions(hits_dict, RESULTS_DIR / "first_hit_statistics.png")

    plot_hadamard_heatmap(hadamard_series, RESULTS_DIR / "hadamard_heatmap.png")

    save_metrics_table(series_dict, RESULTS_DIR / "walk_metrics.csv")
    save_first_hit_table(hits_dict, RESULTS_DIR / "first_hit_table.csv")

    run_decoherence_analysis(
        hadamard_series,
        classical_series,
        FIT_RANGE,
        RESULTS_DIR / "decoherence_exponent.csv",
        RESULTS_DIR / "decoherence_exponent.png",
    )


if __name__ == "__main__":
    main()
