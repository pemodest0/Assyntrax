import math
import shutil
from pathlib import Path
from typing import Sequence
import sys

import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from classical_walk import classical_random_walk_time_series
from quantum_walk import grover_coin, hadamard_coin, quantum_random_walk_time_series

CLASSICAL_LABEL = "Classical"
HADAMARD_LABEL = "Quantum (Hadamard coin)"
GROVER_LABEL = "Quantum (Grover coin)"
STEP_SCHEDULE: Sequence[int] = (10, 100, 1000)

HADAMARD_COIN = hadamard_coin()
GROVER_COIN = grover_coin()
GROVER_INITIAL_STATE = (1.0 / math.sqrt(2.0), 1.0j / math.sqrt(2.0))


def compute_series(n_steps: int) -> dict[str, np.ndarray | int]:
    """Return positions and time series for classical, Hadamard, and Grover walks."""
    positions = np.arange(-n_steps, n_steps + 1)
    classical_series = classical_random_walk_time_series(n_steps)
    hadamard_series = quantum_random_walk_time_series(n_steps, coin=HADAMARD_COIN)
    grover_series = quantum_random_walk_time_series(n_steps, coin=GROVER_COIN, coin_state=GROVER_INITIAL_STATE)
    return {
        "n_steps": n_steps,
        "positions": positions,
        "classical_series": classical_series,
        "hadamard_series": hadamard_series,
        "grover_series": grover_series,
    }


def plot_comparison(
    positions: np.ndarray,
    classical_probs: np.ndarray,
    hadamard_probs: np.ndarray,
    grover_probs: np.ndarray,
    n_steps: int,
    output_path: Path,
) -> None:
    """Plot overlays for the given distributions with wavefunction annotations."""
    fig, ax = plt.subplots(figsize=(10, 6))

    ax.plot(positions, classical_probs, color="black", linewidth=2.0, label=CLASSICAL_LABEL)
    ax.plot(positions, hadamard_probs, color="#6A0DAD", linewidth=2.0, label=HADAMARD_LABEL)
    ax.plot(positions, grover_probs, color="#1f77b4", linewidth=2.0, label=GROVER_LABEL)
    ax.set_xlabel("Position")
    ax.set_ylabel("Probability")
    ax.set_title(f"Final distributions after {n_steps} steps")
    ax.grid(True, linestyle="--", alpha=0.3)
    ax.legend()

    fig.tight_layout()
    fig.savefig(output_path, dpi=300)
    plt.close(fig)
    print(f"Saved {output_path}")




def compute_fourier_spectrum(distribution: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Return frequency axis and magnitude of the discrete Fourier transform."""
    spectrum = np.fft.fftshift(np.fft.fft(distribution))
    magnitude = np.abs(spectrum)
    freqs = np.fft.fftshift(np.fft.fftfreq(distribution.size, d=1.0))
    return freqs, magnitude


def plot_fourier_spectrum(
    classical_probs: np.ndarray,
    hadamard_probs: np.ndarray,
    grover_probs: np.ndarray,
    n_steps: int,
    output_path: Path,
) -> None:
    """Plot Fourier-domain magnitude comparison for the final distributions."""
    classical_freqs, classical_mag = compute_fourier_spectrum(classical_probs)
    hadamard_freqs, hadamard_mag = compute_fourier_spectrum(hadamard_probs)
    grover_freqs, grover_mag = compute_fourier_spectrum(grover_probs)

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(classical_freqs, classical_mag, color="black", linewidth=2.0, label=CLASSICAL_LABEL)
    ax.plot(hadamard_freqs, hadamard_mag, color="#6A0DAD", linewidth=2.0, label=HADAMARD_LABEL)
    ax.plot(grover_freqs, grover_mag, color="#1f77b4", linewidth=2.0, label=GROVER_LABEL)

    ax.set_xlabel("Spatial frequency (1/site)")
    ax.set_ylabel("Fourier magnitude")
    ax.set_title(f"Fourier spectra of final distributions ({n_steps} steps)")
    ax.grid(True, linestyle="--", alpha=0.3)
    ax.legend()

    fig.tight_layout()
    fig.savefig(output_path, dpi=300)
    plt.close(fig)
    print(f"Saved {output_path}")


def main() -> None:
    project_root = Path(__file__).resolve().parent
    results_dir = ROOT / "outputs" / "1d_walks" / "overlays"
    if results_dir.exists():
        shutil.rmtree(results_dir)
    results_dir.mkdir(parents=True, exist_ok=True)

    for n_steps in STEP_SCHEDULE:
        step_data = compute_series(n_steps)
        positions = step_data["positions"]
        classical_series = step_data["classical_series"]
        hadamard_series = step_data["hadamard_series"]
        grover_series = step_data["grover_series"]

        classical_probs = classical_series[-1]
        hadamard_probs = hadamard_series[-1]
        grover_probs = grover_series[-1]

        step_dir = results_dir / f"steps_{n_steps}"
        step_dir.mkdir(parents=True, exist_ok=True)
        plot_comparison(
            positions,
            classical_probs,
            hadamard_probs,
            grover_probs,
            n_steps,
            step_dir / "final_distribution.png",
        )

        plot_fourier_spectrum(
            classical_probs,
            hadamard_probs,
            grover_probs,
            n_steps,
            step_dir / "fourier_spectrum.png",
        )

if __name__ == "__main__":
    main()
