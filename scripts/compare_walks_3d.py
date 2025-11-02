import numpy as np
from pathlib import Path
from typing import Iterable, Sequence, Tuple
import sys

import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401

ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from classical_walk_3d import classical_random_walk_3d
from quantum_walk_3d import grover_coin_3d, quantum_walk_3d_probabilities

STEPS: Sequence[int] = (10,)
RESULTS_DIR = ROOT / "outputs" / "3d_walks"


def slugify(label: str) -> str:
    return (
        label.lower()
        .replace(" ", "_")
        .replace("(", "")
        .replace(")", "")
        .replace("/", "_")
    )


def extract_bars(
    probabilities: np.ndarray,
    max_points: int = 2500,
    threshold: float = 1e-5,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return coordinates and values suitable for 3D bar plotting."""
    coords = np.argwhere(probabilities > threshold)
    values = probabilities[probabilities > threshold]
    if coords.shape[0] == 0:
        return np.array([]), np.array([]), np.array([])

    if coords.shape[0] > max_points:
        idx = np.argsort(values)[-max_points:]
        coords = coords[idx]
        values = values[idx]

    return coords, values, np.sum(probabilities)


def plot_3d_comparison(
    classical_probs: np.ndarray,
    quantum_probs: np.ndarray,
    n_steps: int,
    quantum_label: str,
    output_path: Path,
) -> None:
    size = classical_probs.shape[0]
    origin = size // 2

    classical_coords, classical_values, _ = extract_bars(classical_probs)
    quantum_coords, quantum_values, _ = extract_bars(quantum_probs)

    fig = plt.figure(figsize=(14, 6))
    gs = fig.add_gridspec(1, 2, width_ratios=[1.2, 1.2], wspace=0.18)

    def plot_bars(ax, coords, values, title, cmap="viridis"):
        if coords.size == 0:
            ax.set_title(f"{title}\n(no data)")
            return
        x = coords[:, 0] - origin
        y = coords[:, 1] - origin
        z = coords[:, 2] - origin
        cmap_obj = plt.get_cmap(cmap)
        ax.bar3d(
            x,
            y,
            np.zeros_like(z),
            0.8,
            0.8,
            values,
            shade=True,
            color=cmap_obj(values / values.max()),
        )
        ax.set_title(title)
        ax.set_xlabel("x")
        ax.set_ylabel("y")
        ax.set_zlabel("Probability")
        ax.view_init(elev=30, azim=-45)

    ax1 = fig.add_subplot(gs[0, 0], projection="3d")
    plot_bars(ax1, classical_coords, classical_values, f"Classical random walk ({n_steps} steps)")

    ax2 = fig.add_subplot(gs[0, 1], projection="3d")
    plot_bars(ax2, quantum_coords, quantum_values, f"{quantum_label} ({n_steps} steps)", cmap="plasma")

    fig.suptitle("3D random walk comparison", fontsize=16)
    fig.tight_layout()
    fig.savefig(output_path, dpi=300)
    plt.close(fig)
    print(f"Saved {output_path}")


def plot_slice_heatmap(
    probabilities: np.ndarray,
    title: str,
    output_path: Path,
) -> None:
    """Plot central slices of the 3D distribution."""
    size = probabilities.shape[0]
    origin = size // 2

    xy = probabilities[:, :, origin]
    xz = probabilities[:, origin, :]
    yz = probabilities[origin, :, :]

    vmax = max(xy.max(), xz.max(), yz.max())
    positions = np.arange(-origin, origin + 1)
    extent = (positions[0] - 0.5, positions[-1] + 0.5, positions[0] - 0.5, positions[-1] + 0.5)

    fig, axes = plt.subplots(1, 3, figsize=(12, 4))
    for ax, data, plane in zip(axes, (xy, xz, yz), ("XY plane", "XZ plane", "YZ plane")):
        im = ax.imshow(data, origin="lower", cmap="magma", extent=extent, vmin=0, vmax=vmax)
        ax.set_title(plane)
        ax.set_xlabel("Position")
        ax.set_ylabel("Position")
        fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)

    fig.suptitle(title, fontsize=15)
    fig.tight_layout()
    fig.savefig(output_path, dpi=300)
    plt.close(fig)
    print(f"Saved {output_path}")


def main() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    for n_steps in STEPS:
        classical_probs = classical_random_walk_3d(n_steps)
        quantum_probs = quantum_walk_3d_probabilities(n_steps, coin_matrix=grover_coin_3d())

        base_name = f"{n_steps}_steps"
        plot_3d_comparison(
            classical_probs,
            quantum_probs,
            n_steps,
            "Quantum (Grover coin)",
            RESULTS_DIR / f"comparison_{base_name}.png",
        )
        plot_slice_heatmap(
            classical_probs,
            f"Classical walk slices ({n_steps} steps)",
            RESULTS_DIR / f"classical_slices_{base_name}.png",
        )
        plot_slice_heatmap(
            quantum_probs,
            f"Quantum walk slices ({n_steps} steps)",
            RESULTS_DIR / f"quantum_slices_{base_name}.png",
        )


if __name__ == "__main__":
    main()
