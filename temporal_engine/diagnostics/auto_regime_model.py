"""Modelo automático para rotulagem de regimes a partir de estatísticas."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json

import numpy as np

try:
    import joblib
    from sklearn.ensemble import RandomForestClassifier
except Exception:  # pragma: no cover - optional dependency
    joblib = None
    RandomForestClassifier = None


DEFAULT_MODEL_DIR = Path("models")
DEFAULT_MODEL_PATH = DEFAULT_MODEL_DIR / "auto_regime_model.joblib"
DEFAULT_META_PATH = DEFAULT_MODEL_DIR / "auto_regime_model_meta.json"


FEATURE_NAMES = (
    "mean_x",
    "std_x",
    "abs_mean_x",
    "mean_v",
    "std_v",
    "abs_mean_v",
    "mean_energy",
    "std_energy",
    "energy_p10",
    "energy_p90",
    "percent",
    "transitions_out",
    "segments",
    "mean_local_entropy",
    "mean_local_rr",
    "mean_local_skew",
    "mean_local_kurtosis",
    "mean_acf1",
    "mean_acf2",
    "mean_acf3",
    "mean_acf4",
    "mean_acf5",
    "kinetic_mean",
    "potential_mean",
)


@dataclass(frozen=True)
class AutoRegimeModel:
    model: object
    feature_names: tuple[str, ...]


def _safe_float(value: object, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return float(default)


def _normalize_row(row: dict[str, object]) -> dict[str, float]:
    return {
        "mean_x": _safe_float(row.get("mean_x", row.get("x_mean", 0.0))),
        "std_x": _safe_float(row.get("std_x", 0.0)),
        "abs_mean_x": _safe_float(row.get("abs_mean_x", row.get("abs_x_mean", 0.0))),
        "mean_v": _safe_float(row.get("mean_v", row.get("y_mean", 0.0))),
        "std_v": _safe_float(row.get("std_v", 0.0)),
        "abs_mean_v": _safe_float(row.get("abs_mean_v", row.get("abs_v_mean", 0.0))),
        "mean_energy": _safe_float(row.get("mean_energy", row.get("energy_mean", 0.0))),
        "std_energy": _safe_float(row.get("std_energy", 0.0)),
        "energy_p10": _safe_float(row.get("energy_p10", 0.0)),
        "energy_p90": _safe_float(row.get("energy_p90", 0.0)),
        "percent": _safe_float(row.get("percent", 0.0)),
        "transitions_out": _safe_float(row.get("transitions_out", row.get("transitions", 0.0))),
        "segments": _safe_float(row.get("segments", 0.0)),
        "mean_local_entropy": _safe_float(row.get("mean_local_entropy", 0.0)),
        "mean_local_rr": _safe_float(row.get("mean_local_rr", 0.0)),
        "mean_local_skew": _safe_float(row.get("mean_local_skew", 0.0)),
        "mean_local_kurtosis": _safe_float(row.get("mean_local_kurtosis", 0.0)),
        "mean_acf1": _safe_float(row.get("mean_acf1", 0.0)),
        "mean_acf2": _safe_float(row.get("mean_acf2", 0.0)),
        "mean_acf3": _safe_float(row.get("mean_acf3", 0.0)),
        "mean_acf4": _safe_float(row.get("mean_acf4", 0.0)),
        "mean_acf5": _safe_float(row.get("mean_acf5", 0.0)),
        "kinetic_mean": _safe_float(row.get("kinetic_mean", 0.0)),
        "potential_mean": _safe_float(row.get("potential_mean", 0.0)),
    }


def vector_from_row(row: dict[str, object], feature_names: tuple[str, ...] = FEATURE_NAMES) -> np.ndarray:
    normalized = _normalize_row(row)
    return np.array([normalized.get(name, 0.0) for name in feature_names], dtype=float)


def vector_from_cluster_stats(
    stats: dict[str, float],
    percent: float,
    transitions_out: float,
    feature_names: tuple[str, ...] = FEATURE_NAMES,
) -> np.ndarray:
    row = {
        "mean_x": stats.get("mean_x", 0.0),
        "std_x": stats.get("std_x", 0.0),
        "abs_mean_x": stats.get("abs_mean_x", 0.0),
        "mean_v": stats.get("mean_velocity", stats.get("mean_v", 0.0)),
        "std_v": stats.get("std_velocity", stats.get("std_v", 0.0)),
        "abs_mean_v": stats.get("abs_mean_v", 0.0),
        "mean_energy": stats.get("mean_energy", 0.0),
        "std_energy": stats.get("std_energy", 0.0),
        "energy_p10": stats.get("energy_p10", 0.0),
        "energy_p90": stats.get("energy_p90", 0.0),
        "percent": percent,
        "transitions_out": transitions_out,
        "segments": stats.get("segments", 0.0),
        "mean_local_entropy": stats.get("mean_local_entropy", 0.0),
        "mean_local_rr": stats.get("mean_local_rr", 0.0),
        "mean_local_skew": stats.get("mean_local_skew", 0.0),
        "mean_local_kurtosis": stats.get("mean_local_kurtosis", 0.0),
        "mean_acf1": stats.get("mean_acf1", 0.0),
        "mean_acf2": stats.get("mean_acf2", 0.0),
        "mean_acf3": stats.get("mean_acf3", 0.0),
        "mean_acf4": stats.get("mean_acf4", 0.0),
        "mean_acf5": stats.get("mean_acf5", 0.0),
        "kinetic_mean": stats.get("kinetic_mean", 0.0),
        "potential_mean": stats.get("potential_mean", 0.0),
    }
    return vector_from_row(row, feature_names=feature_names)


def build_training_dataset_with_meta(
    results_root: Path,
) -> tuple[np.ndarray, np.ndarray, list[str]]:
    rows: list[np.ndarray] = []
    labels: list[str] = []
    groups: list[str] = []
    for path in results_root.rglob("summary*.csv"):
        try:
            import csv
            with path.open("r", encoding="utf-8") as handle:
                reader = csv.DictReader(handle)
                for row in reader:
                    regime = str(row.get("regime", "")).strip()
                    if not regime or regime.startswith("state_"):
                        continue
                    rows.append(vector_from_row(row))
                    labels.append(regime)
                    groups.append(str(path))
        except Exception:
            continue
    if not rows:
        raise RuntimeError("Nenhuma linha de treino encontrada em summary*.csv.")
    return np.vstack(rows), np.array(labels, dtype=object), groups


def build_training_dataset(results_root: Path) -> tuple[np.ndarray, np.ndarray]:
    X, y, _ = build_training_dataset_with_meta(results_root)
    return X, y


def _filter_min_count(
    X: np.ndarray, y: np.ndarray, min_count: int
) -> tuple[np.ndarray, np.ndarray]:
    if min_count <= 1:
        return X, y
    unique, counts = np.unique(y, return_counts=True)
    keep_labels = {label for label, count in zip(unique, counts) if count >= min_count}
    if not keep_labels:
        return X, y
    mask = np.array([label in keep_labels for label in y])
    return X[mask], y[mask]


def _balance_samples(
    X: np.ndarray,
    y: np.ndarray,
    mode: str = "oversample",
    target_count: int | None = None,
    max_per_class: int | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    unique, counts = np.unique(y, return_counts=True)
    if not counts.size:
        return X, y
    max_count = int(counts.max())
    desired = target_count or max_count
    if max_per_class is not None:
        desired = min(desired, int(max_per_class))
    rng = np.random.default_rng(42)
    X_out: list[np.ndarray] = []
    y_out: list[np.ndarray] = []
    for label, count in zip(unique, counts):
        idx = np.where(y == label)[0]
        if idx.size == 0:
            continue
        if mode == "oversample":
            if count < desired:
                extra = rng.choice(idx, size=desired - count, replace=True)
                idx = np.concatenate([idx, extra])
            elif count > desired:
                idx = rng.choice(idx, size=desired, replace=False)
        elif mode == "downsample":
            if count > desired:
                idx = rng.choice(idx, size=desired, replace=False)
        else:
            pass
        X_out.append(X[idx])
        y_out.append(y[idx])
    return np.vstack(X_out), np.concatenate(y_out)


def train_auto_regime_model(
    results_root: Path = Path("results"),
    model_path: Path = DEFAULT_MODEL_PATH,
    meta_path: Path = DEFAULT_META_PATH,
    balance: bool = True,
    balance_mode: str = "oversample",
    min_count: int = 1,
    max_per_class: int | None = None,
) -> AutoRegimeModel:
    if RandomForestClassifier is None or joblib is None:
        raise RuntimeError("scikit-learn/joblib não estão disponíveis para treinar o modelo.")

    X, y = build_training_dataset(results_root)
    X, y = _filter_min_count(X, y, min_count=min_count)
    if balance:
        X, y = _balance_samples(X, y, mode=balance_mode, max_per_class=max_per_class)
    model = RandomForestClassifier(
        n_estimators=300,
        random_state=42,
        class_weight="balanced",
        min_samples_leaf=2,
    )
    model.fit(X, y)

    model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, model_path)
    meta_path.write_text(
        json.dumps({"feature_names": FEATURE_NAMES}, indent=2),
        encoding="utf-8",
    )
    return AutoRegimeModel(model=model, feature_names=FEATURE_NAMES)


def load_auto_regime_model(
    model_path: Path = DEFAULT_MODEL_PATH,
    meta_path: Path = DEFAULT_META_PATH,
) -> AutoRegimeModel:
    if joblib is None:
        raise RuntimeError("joblib não está disponível para carregar o modelo.")
    model = joblib.load(model_path)
    feature_names = FEATURE_NAMES
    if meta_path.exists():
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            feature_names = tuple(meta.get("feature_names", FEATURE_NAMES))
        except Exception:
            feature_names = FEATURE_NAMES
    return AutoRegimeModel(model=model, feature_names=feature_names)
