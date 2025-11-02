from pathlib import Path
from typing import Iterable, Sequence, Tuple
import sys

import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401  (needed for 3D projection)

ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from classical_walk_2d import classical_random_walk_2d
from quantum_walk_2d import grover_coin_2d, hadamard_coin_2d, quantum_walk_2d_probabilities

STEPS: Sequence[int] = (20,)
RESULTS_DIR = ROOT / "outputs" / "2d_walks"
CLASSICAL_LABEL = "Classical random walk"


def slugify(label: str) -> str:
    return (
        label.lower()
        .replace(" ", "_")
        .replace("(", "")
        .replace(")", "")
        .replace("/", "_")
        .replace("º", "")
    )


def plot_surface_and_heatmaps(
    positions: np.ndarray,
    classical_probs: np.ndarray,
    quantum_probs: np.ndarray,
    quantum_label: str,
    output_path: Path,
) -> None:
    """Generate a combined figure with surfaces and heatmaps for classical vs quantum walks."""
    x = positions
    y = positions
    X, Y = np.meshgrid(x, y)
    extent = (x[0] - 0.5, x[-1] + 0.5, y[0] - 0.5, y[-1] + 0.5)

    vmax = max(classical_probs.max(), quantum_probs.max())

    fig = plt.figure(figsize=(13, 10))
    gs = fig.add_gridspec(2, 2, height_ratios=[2.2, 1.0], hspace=0.25, wspace=0.18)

    surf_classical = fig.add_subplot(gs[0, 0], projection="3d")
    surf_classical.plot_surface(
        X,
        Y,
        classical_probs,
        cmap="viridis",
        linewidth=0,
        antialiased=False,
        alpha=0.95,
    )
    surf_classical.set_title(f"{CLASSICAL_LABEL} — surface")
    surf_classical.set_xlabel("x")
    surf_classical.set_ylabel("y")
    surf_classical.set_zlabel("Probability")
    surf_classical.set_zlim(0, vmax * 1.1)
    surf_classical.view_init(elev=35, azim=-45)

    surf_quantum = fig.add_subplot(gs[0, 1], projection="3d")
    surf_quantum.plot_surface(
        X,
        Y,
        quantum_probs,
        cmap="plasma",
        linewidth=0,
        antialiased=False,
        alpha=0.95,
    )
    surf_quantum.set_title(f"{quantum_label} — surface")
    surf_quantum.set_xlabel("x")
    surf_quantum.set_ylabel("y")
    surf_quantum.set_zlabel("Probability")
    surf_quantum.set_zlim(0, vmax * 1.1)
    surf_quantum.view_init(elev=35, azim=-45)

    heat_classical = fig.add_subplot(gs[1, 0])
    im1 = heat_classical.imshow(
        classical_probs,
        origin="lower",
        cmap="viridis",
        extent=extent,
    )
    heat_classical.set_title(f"{CLASSICAL_LABEL} — heatmap")
    heat_classical.set_xlabel("x")
    heat_classical.set_ylabel("y")
    fig.colorbar(im1, ax=heat_classical, fraction=0.046, pad=0.04, label="Probability")

    heat_quantum = fig.add_subplot(gs[1, 1])
    im2 = heat_quantum.imshow(
        quantum_probs,
        origin="lower",
        cmap="plasma",
        extent=extent,
    )
    heat_quantum.set_title(f"{quantum_label} — heatmap")
    heat_quantum.set_xlabel("x")
    heat_quantum.set_ylabel("y")
    fig.colorbar(im2, ax=heat_quantum, fraction=0.046, pad=0.04, label="Probability")

    fig.suptitle(f"2D walk comparison after {positions.size // 2} steps", fontsize=16, y=0.98)
    fig.tight_layout(rect=(0, 0, 1, 0.97))
    fig.savefig(output_path, dpi=300)
    plt.close(fig)
    print(f"Saved {output_path}")


def main() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    for n_steps in STEPS:
        size = 2 * n_steps + 1
        positions = np.arange(-n_steps, n_steps + 1)
        classical_probs = classical_random_walk_2d(n_steps)

        quantum_configs: Sequence[Tuple[str, np.ndarray, Iterable[complex] | None]] = (
            ("Quantum (Hadamard tensor Hadamard)", hadamard_coin_2d(), None),
            ("Quantum (Grover diffusion)", grover_coin_2d(), None),
        )

        for label, coin_matrix, state in quantum_configs:
            quantum_probs = quantum_walk_2d_probabilities(
                n_steps,
                coin_matrix=coin_matrix,
                coin_state=state,
            )
            output_path = RESULTS_DIR / f"overview_{slugify(label)}_{n_steps}_steps.png"
            plot_surface_and_heatmaps(
                positions,
                classical_probs,
                quantum_probs,
                label,
                output_path,
            )


if __name__ == "__main__":
    main()
