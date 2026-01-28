from __future__ import annotations

import numpy as np

from spa.engine.diagnostics.auto_regime_model import FEATURE_NAMES
from spa.engine.diagnostics.regime_labels import RegimeClassifier


class _DummyModel:
    def __init__(self, n_features: int) -> None:
        self.n_features_in_ = n_features

    def predict(self, X: np.ndarray) -> np.ndarray:
        return np.array(["dummy"] * X.shape[0], dtype=object)


def test_label_sequence_falls_back_on_feature_mismatch() -> None:
    series = np.array([0.0, 0.2, -0.1, 0.3, -0.2, 0.1])
    embedded = np.column_stack([series[2:], series[1:-1]])
    cluster_labels = np.array([0, 0, 1, 1])
    velocity = np.array([0.1, -0.2, 0.3, -0.1])
    energy = velocity**2 + embedded[:, 0] ** 2
    features = {"velocity": velocity, "energy": energy, "system_type": np.array(["auto"])}

    clf = RegimeClassifier()
    clf.set_auto_model(_DummyModel(len(FEATURE_NAMES)), FEATURE_NAMES[:-1])

    labels = clf.label_sequence(series, cluster_labels, embedded, features)

    assert labels.dtype == object
    assert set(labels.tolist()) == {"state_0", "state_1"}
