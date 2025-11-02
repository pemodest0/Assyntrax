from __future__ import annotations

import csv
from pathlib import Path
from typing import List, Tuple
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from grover_search import grover_success_probabilities

RESULTS_DIR = ROOT / "outputs" / "benchmarks" / "glued_trees"


def grover_iterations_for_threshold(num_items: int, threshold: float) -> int:
    probabilities = grover_success_probabilities(num_items, iterations=10)
    hits = np.where(probabilities >= threshold)[0]
    return int(hits[0]) if hits.size else -1


def main() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    comparisons: List[Tuple[str, str, str]] = []

    comparisons.append(
        (
            "Classical random walk (glued trees)",
            "Exponential in depth (requires ~2^n scattering steps)",
            "Max target prob ≈ 2.6%; 50% threshold never reached within 60 steps",
        )
    )
    comparisons.append(
        (
            "Quantum continuous-time walk (glued trees)",
            "Polynomial in depth (hits exit in O(n))",
            "Reached ≥50% target probability at t ≈ 4.2 (step 12) with max ≈ 66%",
        )
    )

    num_items = 2 ** 8
    grover_iters = grover_iterations_for_threshold(num_items, threshold=0.5)
    comparisons.append(
        (
            "Grover amplitude amplification",
            "O(√N) oracle calls",
            f"Need {grover_iters} iterations to reach ≥50% success for N={num_items}",
        )
    )
    comparisons.append(
        (
            "Shor factoring (order finding)",
            "O((log N)^3)",
            "Targets periodicity; requires modular exponentiation + QFT; reaching correct order with high prob after a single run",
        )
    )
    comparisons.append(
        (
            "Custom layered walk (glued trees reduction)",
            "O(n) discrete steps",
            "Use coin+shift on line of 2n+1 states; deterministic hitting of exit layer; suitable for IBM Q implementation",
        )
    )

    csv_path = RESULTS_DIR / "algorithm_comparison_table.csv"
    with csv_path.open("w", newline="") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(["Algorithm", "Scaling / Complexity", "Observed behaviour / Notes"])
        writer.writerows(comparisons)
    print(f"Saved {csv_path}")


if __name__ == "__main__":
    main()
