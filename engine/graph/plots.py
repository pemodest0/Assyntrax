from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


def plot_timeline_regime(outdir: Path, regimes: np.ndarray, confidence: np.ndarray) -> None:
    fig, ax1 = plt.subplots(figsize=(10, 3))
    ax1.plot(regimes, color="#22d3ee", linewidth=1.5, label="regime")
    ax1.set_title("Regime timeline")
    ax1.set_ylabel("regime")
    ax2 = ax1.twinx()
    ax2.plot(confidence, color="#facc15", linewidth=1.0, label="confidence")
    ax2.set_ylabel("confidence")
    fig.tight_layout()
    fig.savefig(outdir / "timeline_regime.png", dpi=150)
    plt.close(fig)


def plot_transition_matrix(outdir: Path, matrix: np.ndarray) -> None:
    fig, ax = plt.subplots(figsize=(4, 4))
    im = ax.imshow(matrix, cmap="viridis")
    ax.set_title("Transition matrix")
    fig.colorbar(im, ax=ax)
    fig.tight_layout()
    fig.savefig(outdir / "transition_matrix.png", dpi=150)
    plt.close(fig)


def plot_embedding_2d(outdir: Path, embedding: np.ndarray, regimes: np.ndarray) -> None:
    fig, ax = plt.subplots(figsize=(4, 4))
    ax.scatter(embedding[:, 0], embedding[:, 1], c=regimes, s=8, cmap="turbo", alpha=0.8)
    ax.set_title("Embedding 2D")
    fig.tight_layout()
    fig.savefig(outdir / "embedding_2d.png", dpi=150)
    plt.close(fig)


def plot_stretch_hist(outdir: Path, stretch: np.ndarray, regimes: np.ndarray) -> None:
    fig, ax = plt.subplots(figsize=(6, 3))
    ax.hist(stretch, bins=40, color="#38bdf8", alpha=0.7)
    ax.set_title("Stretch histogram")
    fig.tight_layout()
    fig.savefig(outdir / "stretch_hist.png", dpi=150)
    plt.close(fig)
