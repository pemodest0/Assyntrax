from __future__ import annotations

import csv
import warnings
from pathlib import Path

import numpy as np

from engine.diagnostics.auto_regime_model import build_training_dataset_with_meta


def _write_summary(path: Path) -> None:
    rows = [
        {"regime": "alpha", "mean_x": 1.0, "std_x": 0.1},
        {"regime": "beta", "mean_x": -1.0, "std_x": 0.2},
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def test_build_training_dataset_with_meta_warns_on_skipped_files(tmp_path: Path) -> None:
    results_root = tmp_path / "results"
    results_root.mkdir(parents=True)
    _write_summary(results_root / "summary.csv")
    (results_root / "summary_bad.csv").write_bytes(b"\xff")

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        X, y, groups = build_training_dataset_with_meta(results_root)

    assert isinstance(X, np.ndarray)
    assert len(y) == 2
    assert len(groups) == 2
    assert any("Ignorados" in str(w.message) for w in caught)
