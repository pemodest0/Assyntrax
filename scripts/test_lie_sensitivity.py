#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from src.walk_lie.encoding import FeatureBin, HypercubeEncoder
from src.walk_lie.lie_tools import lie_penalty


def main() -> None:
    parser = argparse.ArgumentParser(description="Calcula métrica Λ de comutadores.")
    parser.add_argument("theta_json", type=str, help="JSON com lista de vetores theta")
    args = parser.parse_args()

    data = json.loads(Path(args.theta_json).read_text())
    thetas = [np.array(theta, dtype=float) for theta in data]
    penalty = lie_penalty(np.stack(thetas, axis=0))
    print(f"Λ = {penalty:.4f}")


if __name__ == "__main__":
    main()
