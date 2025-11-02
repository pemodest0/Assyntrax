from __future__ import annotations

from pathlib import Path
from typing import Dict
import sys

import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from classical_walk import simulate_classical_walk
from graph_utils import Graph, cycle_graph, line_graph
from plot_utils import plot_distribution_heatmap, plot_entropy_curves, plot_hitting_time_bars
from quantum_walk import QISKIT_AVAILABLE, QuantumWalkResult, simulate_quantum_walk

OUTPUT_ROOT = ROOT / "outputs" / "1d_walks"
DEFAULT_STEPS = 40
DEFAULT_THRESHOLD = 0.3
DEFAULT_SHOTS = 256
RNG_SEED = 1234


def _title(graph_name: str, descriptor: str) -> str:
    return f"{graph_name} - {descriptor}"


def run_topology(
    graph_name: str,
    graph: Graph,
    start_node: int,
    target_node: int,
    steps: int = DEFAULT_STEPS,
    threshold: float = DEFAULT_THRESHOLD,
    shots: int = DEFAULT_SHOTS,
) -> Dict[str, object]:
    if not QISKIT_AVAILABLE:
        raise RuntimeError("Qiskit is required for the quantum walk simulations.")

    if start_node < 0 or start_node >= graph.num_nodes:
        raise ValueError("start_node is out of range for the provided graph.")
    if target_node < 0 or target_node >= graph.num_nodes:
        raise ValueError("target_node is out of range for the provided graph.")

    scenario_dir = OUTPUT_ROOT / graph_name.lower()
    scenario_dir.mkdir(parents=True, exist_ok=True)

    classical = simulate_classical_walk(
        graph,
        steps,
        start_node=start_node,
        target_node=target_node,
        threshold=threshold,
    )

    quantum_results: Dict[str, QuantumWalkResult] = {}
    for coin in ("hadamard", "grover"):
        result = simulate_quantum_walk(
            graph,
            steps,
            coin=coin,
            start_node=start_node,
            target_node=target_node,
            threshold=threshold,
            measurement="projective",
            shots=shots,
            seed=RNG_SEED,
        )
        quantum_results[coin] = result

        coin_dir = scenario_dir / coin
        coin_dir.mkdir(parents=True, exist_ok=True)

        fig = plot_distribution_heatmap(
            result.distributions,
            result.positions,
            _title(graph.name, f"Quantum ({coin.capitalize()} coin) - ideal"),
            coin_dir / "distribution_heatmap_ideal.png",
        )
        plt.close(fig)

        if result.measurement_distributions is not None:
            fig = plot_distribution_heatmap(
                result.measurement_distributions,
                result.positions,
                _title(graph.name, f"Quantum ({coin.capitalize()} coin) - projective"),
                coin_dir / "distribution_heatmap_projective.png",
            )
            plt.close(fig)

    fig = plot_distribution_heatmap(
        classical.distributions,
        classical.positions,
        _title(graph.name, "Classical random walk"),
        scenario_dir / "distribution_heatmap_classical.png",
    )
    plt.close(fig)

    entropy_map = {f"{graph.name} classical": classical.entropies}
    hitting_data = [(f"{graph.name} classical", classical.hitting_time)]

    for coin, result in quantum_results.items():
        label = f"{graph.name} quantum ({coin})"
        entropy_map[f"{label} - ideal"] = result.entropies
        hitting_data.append((f"{label} - ideal", result.hitting_time))
        if result.measurement_entropies is not None:
            entropy_map[f"{label} - projective"] = result.measurement_entropies
            hitting_data.append((f"{label} - projective", result.measurement_hitting_time))

    fig = plot_entropy_curves(entropy_map, scenario_dir / "entropy_comparison.png")
    plt.close(fig)

    fig = plot_hitting_time_bars(hitting_data, scenario_dir / "hitting_time_comparison.png")
    plt.close(fig)

    return {
        "graph": graph,
        "classical": classical,
        "quantum": quantum_results,
        "scenario_dir": scenario_dir,
    }


def main() -> Dict[str, object]:
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)

    line_graph_size = 21
    line_start = line_graph_size // 2
    line_target = line_graph_size - 1
    line = line_graph(line_graph_size)

    cycle_graph_size = 20
    cycle_start = 0
    cycle_target = cycle_graph_size // 2
    cycle = cycle_graph(cycle_graph_size)

    summary: Dict[str, object] = {}
    summary["line"] = run_topology(
        "Line",
        line,
        start_node=line_start,
        target_node=line_target,
        steps=DEFAULT_STEPS,
        threshold=DEFAULT_THRESHOLD,
        shots=DEFAULT_SHOTS,
    )
    summary["cycle"] = run_topology(
        "Cycle",
        cycle,
        start_node=cycle_start,
        target_node=cycle_target,
        steps=DEFAULT_STEPS,
        threshold=DEFAULT_THRESHOLD,
        shots=DEFAULT_SHOTS,
    )
    return summary


if __name__ == "__main__":
    results = main()
    for name, data in results.items():
        graph = data["graph"]
        classical = data["classical"]
        print(f"{name.capitalize()} graph ({graph.num_nodes} nodes)")
        print(f"  Classical hitting time: {classical.hitting_time}")
        for coin, result in data["quantum"].items():
            print(
                f"  Quantum {coin.capitalize()} ideal hitting time: {result.hitting_time}; "
                f"projective: {result.measurement_hitting_time}"
            )
