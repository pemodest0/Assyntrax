from __future__ import annotations

import numpy as np
from sklearn.cluster import KMeans


def build_microstates(embedded: np.ndarray, n_micro: int, seed: int = 7) -> tuple[np.ndarray, np.ndarray]:
    km = KMeans(n_clusters=n_micro, random_state=seed, n_init=10)
    labels = km.fit_predict(embedded)
    return labels, km.cluster_centers_
