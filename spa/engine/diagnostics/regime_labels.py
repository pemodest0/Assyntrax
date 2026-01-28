"""Regime detection labels and clustering utilities."""

from __future__ import annotations

from pathlib import Path
import csv
import hashlib
import json

import numpy as np
from sklearn.cluster import DBSCAN, KMeans
from sklearn.preprocessing import StandardScaler

from spa.engine.diagnostics.auto_regime_model import (
    FEATURE_NAMES,
    load_auto_regime_model,
    vector_from_cluster_stats,
)
from spa.engine.diagnostics.macro_context import (
    annotate_transitions,
    load_macro_events,
)

try:
    import matplotlib.pyplot as plt
except Exception:  # pragma: no cover - optional plotting dependency
    plt = None

try:
    from hdbscan import HDBSCAN
except Exception:  # pragma: no cover - optional dependency fallback
    HDBSCAN = None


class RegimeClassifier:
    def __init__(
        self,
        tau: int = 1,
        m: int = 3,
        clustering_method: str = "hdbscan",
        cluster_params: dict | None = None,
        alpha: float = 1.0,
    ):
        """Inicializa o classificador de regime.

        Args:
            tau: Atraso (número de passos) usado no embedding de Takens.
            m: Dimensão do embedding (número de atrasos). Para proxy de velocidade e
                aceleração, valores típicos são 2 ou 3.
            clustering_method: Algoritmo de clusterização a ser usado; opções: 'hdbscan',
                'dbscan', 'kmeans'. Se 'kmeans' for usado, o parâmetro `cluster_params`
                deve incluir 'n_clusters'.
            cluster_params: Parâmetros específicos do algoritmo de clusterização, como
                `eps` e `min_samples` para DBSCAN, `min_cluster_size` para HDBSCAN, ou
                `n_clusters` para k-means.
            alpha: Fator usado na fórmula de energia E_t = x_t**2 + alpha * v_t**2.
        """
        self.tau = tau
        self.m = m
        self.method = clustering_method
        self.params = cluster_params or {}
        self.alpha = alpha
        self.last_cluster_stats: dict[int, dict[str, float]] | None = None
        self.auto_model = None
        self.auto_feature_names: tuple[str, ...] | None = None

    def set_auto_model(self, model: object, feature_names: tuple[str, ...]) -> None:
        """Registra um modelo automático de regimes carregado externamente."""
        self.auto_model = model
        self.auto_feature_names = feature_names

    def shannon_entropy(self, embedded: np.ndarray, bins: int = 10) -> float:
        """Calcula entropia de Shannon de estados embutidos via discretização.

        Args:
            embedded: Matriz do embedding (amostras x dimensões).
            bins: Número de bins por dimensão para discretizar.

        Returns:
            Entropia em bits (float).

        Raises:
            ValueError: Se o embedding não for 2-D.
        """
        data = np.asarray(embedded)
        if data.ndim != 2:
            raise ValueError("embedded must be 2-D")
        if data.shape[0] == 0:
            return float("nan")

        edges = [
            np.linspace(np.nanmin(data[:, i]), np.nanmax(data[:, i]), bins + 1)
            for i in range(data.shape[1])
        ]
        digitized = [
            np.clip(np.digitize(data[:, i], edges[i]) - 1, 0, bins - 1)
            for i in range(data.shape[1])
        ]
        tokens = np.stack(digitized, axis=1)
        unique, counts = np.unique(tokens, axis=0, return_counts=True)
        probs = counts / counts.sum()
        entropy = -np.sum(probs * np.log2(probs + 1e-12))
        _ = unique
        return float(entropy)

    def recurrence_rate(
        self,
        embedded: np.ndarray,
        epsilon: float | None = None,
        percentile: float = 10.0,
        max_points: int = 2000,
    ) -> float:
        """Calcula a taxa de recorrência com base em distâncias no embedding.

        Args:
            embedded: Matriz do embedding (amostras x dimensões).
            epsilon: Raio para recorrência. Se None, usa percentil das distâncias.
            percentile: Percentil usado para definir epsilon se não fornecido.
            max_points: Limite de amostras para reduzir custo O(n^2).

        Returns:
            Taxa de recorrência no intervalo [0, 1].

        Raises:
            ValueError: Se o embedding não for 2-D.
        """
        data = np.asarray(embedded)
        if data.ndim != 2:
            raise ValueError("embedded must be 2-D")
        n = data.shape[0]
        if n == 0:
            return float("nan")
        if n > max_points:
            idx = np.random.default_rng(42).choice(n, size=max_points, replace=False)
            data = data[idx]
            n = data.shape[0]

        diffs = data[:, None, :] - data[None, :, :]
        dists = np.linalg.norm(diffs, axis=2)
        if epsilon is None:
            tri = dists[np.triu_indices(n, k=1)]
            epsilon = np.percentile(tri, percentile) if tri.size else 0.0
        recurrence = (dists <= epsilon).mean()
        return float(recurrence)

    def scan_embeddings(
        self,
        series: np.ndarray,
        tau_range: range = range(1, 11),
        m_range: range = range(2, 6),
        bins: int = 10,
        rr_percentile: float = 10.0,
    ) -> list[dict[str, float]]:
        """Avalia entropia e recorrência para vários pares (m, τ).

        Args:
            series: Série temporal 1-D.
            tau_range: Intervalo de atrasos a testar.
            m_range: Intervalo de dimensões a testar.
            bins: Número de bins para entropia discreta.
            rr_percentile: Percentil usado para epsilon na recorrência.

        Returns:
            Lista de dicionários com métricas por par (m, τ).

        Raises:
            ValueError: Se nenhum embedding puder ser construído.
        """
        metrics: list[dict[str, float]] = []
        for m in m_range:
            for tau in tau_range:
                self.m = m
                self.tau = tau
                try:
                    embedded = self.embed(series)
                except ValueError:
                    continue
                entropy = self.shannon_entropy(embedded, bins=bins)
                rr = self.recurrence_rate(embedded, percentile=rr_percentile)
                metrics.append(
                    {
                        "m": int(m),
                        "tau": int(tau),
                        "entropy": float(entropy),
                        "recurrence_rate": float(rr),
                        "n_points": int(embedded.shape[0]),
                    }
                )
        if not metrics:
            raise ValueError("no valid embeddings found for the provided ranges")
        return metrics

    def select_embedding(
        self, metrics: list[dict[str, float]], criterion: str = "min_entropy"
    ) -> tuple[int, int]:
        """Seleciona o melhor par (m, τ) a partir de métricas calculadas.

        Args:
            metrics: Lista com dicionários contendo métricas.
            criterion: 'min_entropy' ou 'max_contrast'.

        Returns:
            Tupla (m, τ) selecionada.

        Raises:
            ValueError: Se o critério for desconhecido.
        """
        if not metrics:
            raise ValueError("metrics list is empty")
        if criterion == "min_entropy":
            best = min(metrics, key=lambda item: item["entropy"])
        elif criterion == "max_contrast":
            best = max(
                metrics,
                key=lambda item: item["entropy"]
                / max(item["recurrence_rate"], 1e-6),
            )
        else:
            raise ValueError(f"Unknown selection criterion: {criterion}")
        return int(best["m"]), int(best["tau"])

    def embed(self, series: np.ndarray) -> np.ndarray:
        """Gera o embedding de Takens para uma série 1-D.

        Args:
            series: Série temporal 1-D com tamanho N.

        Returns:
            Matriz 2-D de tamanho (N - (m-1)*tau, m) com cada linha
            [x_t, x_{t-τ}, x_{t-2τ}, ..., x_{t-(m-1)τ}].

        Raises:
            ValueError: Se a série não for 1-D ou for curta demais.

        Example:
            >>> RegimeClassifier(tau=1, m=3).embed(np.array([1, 2, 3, 4, 5]))
            array([[3, 2, 1],
                   [4, 3, 2],
                   [5, 4, 3]])

        Nota: NaNs devem ser removidos ou propagados antes do embedding.
        """
        values = np.asarray(series)
        if values.ndim != 1:
            raise ValueError("series must be a 1-D array")
        min_len = (self.m - 1) * self.tau + 1
        if values.size < min_len:
            raise ValueError("series is too short for the requested embedding")

        embed_len = values.size - (self.m - 1) * self.tau
        columns = [
            values[(self.m - 1 - lag) * self.tau : (self.m - 1 - lag) * self.tau + embed_len]
            for lag in range(self.m)
        ]
        return np.column_stack(columns)

    def compute_velocity(self, series: np.ndarray) -> np.ndarray:
        """Calcula v_t = x_t - x_{t-τ} alinhado ao embedding.

        Args:
            series: Série temporal 1-D.

        Returns:
            Vetor 1-D com o mesmo comprimento do embedding.

        Raises:
            ValueError: Se a série for curta demais.
        """
        values = np.asarray(series)
        min_len = (self.m - 1) * self.tau + 1
        if values.size < min_len:
            raise ValueError("series is too short for the requested embedding")

        start = (self.m - 1) * self.tau
        return values[start:] - values[start - self.tau : values.size - self.tau]

    def compute_acceleration(self, series: np.ndarray) -> np.ndarray | None:
        """Calcula a_t = x_t - 2x_{t-τ} + x_{t-2τ} alinhado ao embedding.

        Args:
            series: Série temporal 1-D.

        Returns:
            Vetor 1-D com o mesmo comprimento do embedding, ou None se m < 3.

        Raises:
            ValueError: Se a série for curta demais.
        """
        if self.m < 3:
            return None

        values = np.asarray(series)
        min_len = (self.m - 1) * self.tau + 1
        if values.size < min_len:
            raise ValueError("series is too short for the requested embedding")

        start = (self.m - 1) * self.tau
        return (
            values[start:]
            - 2 * values[start - self.tau : values.size - self.tau]
            + values[start - 2 * self.tau : values.size - 2 * self.tau]
        )

    def compute_energy(self, x: np.ndarray, v: np.ndarray) -> np.ndarray:
        """Calcula energia E_t = x_t**2 + alpha * v_t**2.

        Args:
            x: Vetor de posição alinhado ao embedding.
            v: Vetor de velocidade alinhado ao embedding.

        Returns:
            Vetor 1-D de energias.
        """
        return x**2 + self.alpha * v**2

    def compute_local_features(
        self, series: np.ndarray, window: int = 50, bins: int = 10
    ) -> dict[str, np.ndarray]:
        """Calcula features locais em janelas deslizantes.

        Args:
            series: Série temporal 1-D alinhada ao embedding.
            window: Tamanho da janela para estatísticas locais.
            bins: Número de bins para entropia local.

        Returns:
            Dicionário com arrays 1-D alinhados ao embedding.
        """
        values = np.asarray(series, dtype=float)
        n = values.size
        if n == 0:
            return {}
        w = max(5, int(window))
        half = w // 2

        def _window_slice(idx: int) -> np.ndarray:
            start = max(0, idx - half)
            end = min(n, idx + half + 1)
            return values[start:end]

        local_entropy = np.zeros(n)
        local_rr = np.zeros(n)
        local_skew = np.zeros(n)
        local_kurt = np.zeros(n)
        acf1 = np.zeros(n)
        acf2 = np.zeros(n)
        acf3 = np.zeros(n)
        acf4 = np.zeros(n)
        acf5 = np.zeros(n)

        for i in range(n):
            window_vals = _window_slice(i)
            if window_vals.size < 3:
                continue
            hist, _ = np.histogram(window_vals, bins=bins, density=True)
            probs = hist / (hist.sum() + 1e-12)
            local_entropy[i] = -np.sum(probs * np.log2(probs + 1e-12))

            diffs = np.abs(window_vals[:, None] - window_vals[None, :])
            tri = diffs[np.triu_indices(diffs.shape[0], k=1)]
            eps = np.percentile(tri, 10) if tri.size else 0.0
            local_rr[i] = float((diffs <= eps).mean())

            mean = np.mean(window_vals)
            std = np.std(window_vals) + 1e-12
            centered = (window_vals - mean) / std
            local_skew[i] = float(np.mean(centered**3))
            local_kurt[i] = float(np.mean(centered**4) - 3.0)

            for lag, target in zip(
                [1, 2, 3, 4, 5], [acf1, acf2, acf3, acf4, acf5]
            ):
                if window_vals.size > lag:
                    v0 = window_vals[:-lag]
                    v1 = window_vals[lag:]
                    denom = np.std(v0) * np.std(v1) + 1e-12
                    target[i] = float(np.corrcoef(v0, v1)[0, 1]) if denom > 0 else 0.0

        return {
            "local_entropy": local_entropy,
            "local_rr": local_rr,
            "local_skew": local_skew,
            "local_kurtosis": local_kurt,
            "acf1": acf1,
            "acf2": acf2,
            "acf3": acf3,
            "acf4": acf4,
            "acf5": acf5,
        }

    def cluster_states(
        self, embedded: np.ndarray, features: dict[str, np.ndarray]
    ) -> np.ndarray:
        """Clusteriza estados usando embedding e features adicionais.

        Args:
            embedded: Matriz do embedding (amostras x dimensões).
            features: Dicionário com features adicionais alinhadas.

        Returns:
            Vetor de rótulos de cluster.

        Raises:
            ValueError: Se houver inconsistência de tamanhos ou método inválido.
        """
        columns = [embedded]
        for name, values in features.items():
            if values.shape[0] != embedded.shape[0]:
                raise ValueError(f"feature '{name}' length does not match embedding")
            if values.ndim == 1:
                columns.append(values[:, None])
            elif values.ndim == 2:
                columns.append(values)
            else:
                raise ValueError(f"feature '{name}' must be 1-D or 2-D")

        combined = np.hstack(columns) if len(columns) > 1 else embedded
        # Normalização é necessária para evitar que escalas diferentes dominem o clustering.
        scaled = StandardScaler().fit_transform(combined)

        method = self.method.lower()
        def _filter_params(allowed: set[str]) -> dict:
            return {key: value for key, value in self.params.items() if key in allowed}
        n_samples = scaled.shape[0]
        default_min_cluster = max(5, int(0.005 * n_samples))
        default_min_samples = max(3, int(0.002 * n_samples))
        merge_small_clusters = bool(self.params.get("merge_small_clusters", True))
        merge_min_pct = float(self.params.get("merge_min_pct", 0.005))
        if method == "hdbscan":
            if HDBSCAN is None:
                model = DBSCAN(**_filter_params({"eps", "min_samples", "metric", "p", "algorithm", "leaf_size"}))
                labels = model.fit_predict(scaled)
                if not merge_small_clusters:
                    return labels
                return self._merge_small_clusters(
                    labels, scaled, default_min_cluster, merge_min_pct
                )
            # Remover chaves que não pertencem ao HDBSCAN
            params = {
                key: value
                for key, value in self.params.items()
                if key
                not in {
                    "merge_small_clusters",
                    "merge_min_pct",
                    "merge_max_distance",
                    "score_small_cluster_penalty",
                    "score_max_clusters",
                    "score_too_many_penalty",
                }
            }
            params.setdefault("min_cluster_size", default_min_cluster)
            params.setdefault("min_samples", default_min_samples)
            model = HDBSCAN(**params)
            labels = model.fit_predict(scaled)
            if not merge_small_clusters:
                return labels
            return self._merge_small_clusters(
                labels,
                scaled,
                int(params["min_cluster_size"]),
                merge_min_pct,
            )
        if method == "dbscan":
            model = DBSCAN(**_filter_params({"eps", "min_samples", "metric", "p", "algorithm", "leaf_size"}))
            labels = model.fit_predict(scaled)
            if not merge_small_clusters:
                return labels
            return self._merge_small_clusters(
                labels, scaled, default_min_cluster, merge_min_pct
            )
        if method == "kmeans":
            model = KMeans(**_filter_params({"n_clusters", "random_state", "n_init", "max_iter", "tol", "algorithm"}))
            labels = model.fit_predict(scaled)
            if not merge_small_clusters:
                return labels
            return self._merge_small_clusters(
                labels, scaled, default_min_cluster, merge_min_pct
            )

        if method == "auto":
            return self._auto_cluster(scaled)

        raise ValueError(f"Unknown clustering method: {self.method}")

    def _auto_cluster(self, scaled: np.ndarray) -> np.ndarray:
        """Seleciona automaticamente entre HDBSCAN e KMeans com base em score."""
        candidates: list[tuple[str, np.ndarray, float]] = []
        # HDBSCAN
        if HDBSCAN is not None:
            params = {
                key: value
                for key, value in self.params.items()
                if key
                not in {
                    "n_clusters",
                    "merge_small_clusters",
                    "merge_min_pct",
                    "merge_max_distance",
                    "score_small_cluster_penalty",
                    "score_max_clusters",
                    "score_too_many_penalty",
                }
            }
            params.setdefault("min_cluster_size", max(5, int(0.005 * scaled.shape[0])))
            params.setdefault("min_samples", max(3, int(0.002 * scaled.shape[0])))
            labels = HDBSCAN(**params).fit_predict(scaled)
            score = self._cluster_score(scaled, labels)
            candidates.append(("hdbscan", labels, score))
        # KMeans
        params = {key: value for key, value in self.params.items() if key in {"n_clusters", "random_state", "n_init"}}
        params.setdefault("n_clusters", 3)
        labels = KMeans(**params).fit_predict(scaled)
        score = self._cluster_score(scaled, labels)
        candidates.append(("kmeans", labels, score))

        best = max(candidates, key=lambda item: item[2])
        return best[1]

    def _cluster_score(self, scaled: np.ndarray, labels: np.ndarray) -> float:
        """Avalia a qualidade de clustering usando DBCV (se disponível) ou silhouette.

        Aplica penalidade leve para clusters muito pequenos para evitar overclustering.
        """
        labels = np.asarray(labels)
        unique = np.unique(labels[labels != -1])
        if unique.size <= 1:
            return -1.0
        n = labels.size
        min_count = max(5, int(0.005 * n))
        counts = {lab: int(np.sum(labels == lab)) for lab in unique}
        small_clusters = sum(1 for count in counts.values() if count < min_count)
        penalty = float(self.params.get("score_small_cluster_penalty", 0.05)) * small_clusters
        max_clusters = int(self.params.get("score_max_clusters", 12))
        if unique.size > max_clusters:
            penalty += float(self.params.get("score_too_many_penalty", 0.02)) * (unique.size - max_clusters)
        try:
            from hdbscan.validity import validity_index

            return float(validity_index(scaled, labels)) - penalty
        except Exception:
            pass
        try:
            from sklearn.metrics import silhouette_score

            mask = labels != -1
            if mask.sum() < 2:
                return -1.0
            return float(silhouette_score(scaled[mask], labels[mask])) - penalty
        except Exception:
            return -1.0 - penalty

    def _merge_small_clusters(
        self,
        labels: np.ndarray,
        data: np.ndarray,
        min_cluster_size: int,
        min_pct: float,
    ) -> np.ndarray:
        labels = np.asarray(labels).copy()
        if labels.size == 0:
            return labels
        unique, counts = np.unique(labels, return_counts=True)
        if unique.size <= 1:
            return labels
        min_count = max(min_cluster_size, int(min_pct * labels.size))
        large_labels = []
        small_labels = []
        for label, count in zip(unique, counts):
            if label == -1 or count < min_count:
                small_labels.append(label)
            else:
                large_labels.append(label)
        if not large_labels:
            return labels

        centroids = {}
        for label in large_labels:
            centroids[label] = np.nanmean(data[labels == label], axis=0)

        max_distance = self.params.get("merge_max_distance")
        if max_distance is None and len(large_labels) >= 2:
            centers = np.stack([centroids[label] for label in large_labels], axis=0)
            diffs = centers[:, None, :] - centers[None, :, :]
            dists = np.linalg.norm(diffs, axis=2)
            tri = dists[np.triu_indices(dists.shape[0], k=1)]
            if tri.size:
                max_distance = float(np.percentile(tri, 75))

        for label in small_labels:
            idx = np.where(labels == label)[0]
            if idx.size == 0:
                continue
            cluster_center = np.nanmean(data[idx], axis=0)
            distances = {
                big: float(np.linalg.norm(cluster_center - centroids[big]))
                for big in large_labels
            }
            nearest = min(distances, key=distances.get)
            if max_distance is not None and distances[nearest] > max_distance:
                labels[idx] = -1
                continue
            labels[idx] = nearest
        return labels

    def label_sequence(
        self,
        series: np.ndarray,
        cluster_labels: np.ndarray,
        embedded: np.ndarray,
        features: dict[str, np.ndarray],
    ) -> np.ndarray:
        """Rotula os clusters em regimes físicos ou genéricos.

        Args:
            series: Série temporal 1-D original (usada para validações).
            cluster_labels: Rótulos de cluster por ponto do embedding.
            embedded: Matriz do embedding (amostras x dimensões).
            features: Dicionário de features alinhadas (ex.: 'velocity', 'energy').

        Returns:
            Vetor de strings com rótulos humano-legíveis por amostra.

        Raises:
            ValueError: Se faltarem features obrigatórias ou dimensões inválidas.
        """
        _ = series
        labels = np.asarray(cluster_labels)
        if labels.shape[0] != embedded.shape[0]:
            raise ValueError("cluster_labels length does not match embedding")
        if "velocity" not in features or "energy" not in features:
            raise ValueError("features must include 'velocity' and 'energy'")

        velocity = np.asarray(features["velocity"])
        energy = np.asarray(features["energy"])
        if velocity.shape[0] != embedded.shape[0] or energy.shape[0] != embedded.shape[0]:
            raise ValueError("feature lengths do not match embedding")

        energy_crit = np.nanmedian(energy)
        x_vals = embedded[:, 0]
        abs_x = np.abs(x_vals)
        abs_x_med = np.nanmedian(abs_x)
        v_std_global = np.nanstd(velocity)
        unique_labels, counts = np.unique(labels, return_counts=True)
        min_count = counts.min() if counts.size else 0

        cluster_stats: dict[int, dict[str, float]] = {}
        cluster_name_map: dict[int, str] = {}

        for label in unique_labels:
            mask = labels == label
            x_cluster = x_vals[mask]
            v_cluster = velocity[mask]
            e_cluster = energy[mask]
            mean_x = float(np.nanmean(x_cluster))
            mean_e = float(np.nanmean(e_cluster))
            v_mean = float(np.nanmean(v_cluster))
            v_std = float(np.nanstd(v_cluster))
            x_std = float(np.nanstd(x_cluster))
            e_std = float(np.nanstd(e_cluster))
            abs_mean_x = float(np.nanmean(np.abs(x_cluster)))
            abs_mean_v = float(np.nanmean(np.abs(v_cluster)))
            e_p10 = float(np.nanpercentile(e_cluster, 10)) if e_cluster.size else 0.0
            e_p90 = float(np.nanpercentile(e_cluster, 90)) if e_cluster.size else 0.0
            cluster_stats[int(label)] = {
                "mean_x": mean_x,
                "std_x": x_std,
                "abs_mean_x": abs_mean_x,
                "mean_energy": mean_e,
                "std_energy": e_std,
                "energy_p10": e_p10,
                "energy_p90": e_p90,
                "mean_velocity": v_mean,
                "std_velocity": v_std,
                "abs_mean_v": abs_mean_v,
                "count": float(np.sum(mask)),
            }

            cluster_name_map[int(label)] = f"state_{label}"

        system_type = features.get("system_type")
        if isinstance(system_type, np.ndarray) and system_type.size == 1:
            system_type = str(system_type.item())
        if isinstance(system_type, str):
            system_type = system_type.lower().strip()
        else:
            system_type = None

        for label in unique_labels:
            stats = cluster_stats[int(label)]
            mean_x = stats["mean_x"]
            mean_e = stats["mean_energy"]
            v_mean = stats["mean_velocity"]
            v_std = stats["std_velocity"]
            count = int(stats["count"])

            high_energy = mean_e > energy_crit
            near_zero = abs(mean_x) <= 0.5 * abs_x_med if abs_x_med > 0 else abs(mean_x) < 1e-12
            alternating_v = abs(v_mean) <= 0.25 * v_std_global and v_std >= 0.75 * v_std_global
            persistent_v = abs(v_mean) >= 0.5 * v_std_global

            if system_type == "pendulo":
                if high_energy and near_zero:
                    cluster_name_map[int(label)] = "separatrix"
                elif (not high_energy) and alternating_v:
                    cluster_name_map[int(label)] = "libration"
                elif (not high_energy) and persistent_v:
                    cluster_name_map[int(label)] = "rotation"
            elif system_type == "duffing":
                near_zero_duffing = abs_mean_x <= 0.7 * abs_x_med if abs_x_med > 0 else abs_mean_x < 1e-12
                if (high_energy and near_zero_duffing) or (count == min_count and high_energy):
                    cluster_name_map[int(label)] = "transicao"
                elif mean_x < 0:
                    cluster_name_map[int(label)] = "poco_esquerdo"
                else:
                    cluster_name_map[int(label)] = "poco_direito"
            elif system_type == "lorenz":
                xyz = features.get("xyz")
                mean_x_lobe = mean_x
                mean_y_lobe = 0.0
                z_std = 0.0
                if isinstance(xyz, np.ndarray) and xyz.shape[0] == embedded.shape[0]:
                    x_vals = xyz[:, 0][mask]
                    y_vals = xyz[:, 1][mask]
                    z_vals = xyz[:, 2][mask]
                    mean_x_lobe = float(np.nanmean(x_vals))
                    mean_y_lobe = float(np.nanmean(y_vals))
                    z_std = float(np.nanstd(z_vals))
                # Transição: energia alta, região próxima do eixo central ou cluster muito pequeno.
                central_band = abs(mean_x_lobe) <= 0.2 * abs_x_med if abs_x_med > 0 else abs(mean_x_lobe) < 1e-12
                if high_energy or z_std > np.nanmedian(np.abs(energy)) or central_band or count == min_count:
                    cluster_name_map[int(label)] = "transicao"
                else:
                    lobe_score = mean_x_lobe + mean_y_lobe
                    if lobe_score >= 0:
                        cluster_name_map[int(label)] = "asa_direita"
                    else:
                        cluster_name_map[int(label)] = "asa_esquerda"
            elif system_type in {"auto", "automatico"}:
                try:
                    if self.auto_model is None:
                        loaded = load_auto_regime_model()
                        self.auto_model = loaded.model
                        self.auto_feature_names = loaded.feature_names
                    feature_names = self.auto_feature_names or FEATURE_NAMES
                    total = labels.size
                    percent = float(count / total * 100.0) if total else 0.0
                    transitions_out = 0.0
                    if labels.size > 1:
                        changes = labels[1:] != labels[:-1]
                        for idx, changed in enumerate(changes, start=1):
                            if changed and int(labels[idx - 1]) == int(label):
                                transitions_out += 1.0
                    segments = 0.0
                    if labels.size > 0:
                        current = labels[0]
                        if int(current) == int(label):
                            segments += 1.0
                        for value in labels[1:]:
                            if value != current:
                                current = value
                                if int(current) == int(label):
                                    segments += 1.0
                    stats["segments"] = segments
                    vector = vector_from_cluster_stats(
                        stats,
                        percent=percent,
                        transitions_out=transitions_out,
                        feature_names=feature_names,
                    )
                    expected = getattr(self.auto_model, "n_features_in_", None)
                    if expected is not None and vector.shape[0] != int(expected):
                        raise ValueError(
                            f"Auto model espera {expected} features, mas recebeu {vector.shape[0]}"
                        )
                    predicted = self.auto_model.predict(vector.reshape(1, -1))[0]
                    cluster_name_map[int(label)] = str(predicted)
                except Exception:
                    cluster_name_map[int(label)] = f"state_{label}"

        self.last_cluster_stats = cluster_stats
        return np.array([cluster_name_map[int(lbl)] for lbl in labels], dtype=object)

    def _smooth_labels(self, labels: np.ndarray, min_run: int = 5) -> np.ndarray:
        """Suaviza rótulos removendo segmentos muito curtos."""
        if min_run <= 1:
            return labels
        values = np.asarray(labels, dtype=object).copy()
        n = values.size
        if n == 0:
            return values

        start = 0
        while start < n:
            current = values[start]
            end = start + 1
            while end < n and values[end] == current:
                end += 1
            run_len = end - start
            if run_len < min_run:
                left_label = values[start - 1] if start > 0 else None
                right_label = values[end] if end < n else None
                if left_label is not None and right_label is not None and left_label == right_label:
                    values[start:end] = left_label
                elif left_label is None and right_label is not None:
                    values[start:end] = right_label
                elif right_label is None and left_label is not None:
                    values[start:end] = left_label
                else:
                    values[start:end] = left_label if left_label is not None else right_label
            start = end
        return values

    def run_full_analysis(
        self,
        series: np.ndarray,
        output_dir: str | Path,
        dates: np.ndarray | None = None,
        system_type: str | None = None,
        filename_suffix: str = "",
        tau_range: range = range(1, 11),
        m_range: range = range(2, 6),
        selection_criterion: str = "min_entropy",
        bins: int = 10,
        rr_percentile: float = 10.0,
        smooth_labels: bool = True,
        min_run: int = 3,
        local_window: int = 50,
        generate_plots: bool = True,
        generate_report: bool = True,
        macro_events_path: str | Path | None = None,
        macro_asset: str | None = None,
        macro_window_days: int = 3,
        write_meta: bool = True,
        write_confidence: bool = True,
        write_master_plot: bool = True,
    ) -> dict[str, object]:
        """Executa a pipeline completa de detecção e rotulagem de regimes.

        Args:
            series: Série temporal 1-D.
            output_dir: Pasta onde os arquivos serão salvos.
            system_type: Tipo do sistema ('pendulo', 'duffing') ou None.
            filename_suffix: Sufixo adicionado aos nomes dos arquivos gerados.
            tau_range: Intervalo de τ para busca.
            m_range: Intervalo de m para busca.
            selection_criterion: Critério para seleção de (m, τ).
            bins: Número de bins para entropia.
            rr_percentile: Percentil para epsilon na recorrência.

        Returns:
            Dicionário com os principais resultados e caminhos gerados.

        Raises:
            ValueError: Se não for possível construir embeddings válidos.
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        metrics = self.scan_embeddings(
            series, tau_range=tau_range, m_range=m_range, bins=bins, rr_percentile=rr_percentile
        )
        best_m, best_tau = self.select_embedding(metrics, criterion=selection_criterion)
        self.m = best_m
        self.tau = best_tau

        embedded = self.embed(series)
        velocity = self.compute_velocity(series)
        energy = self.compute_energy(embedded[:, 0], velocity)
        local_features = self.compute_local_features(embedded[:, 0], window=local_window)
        cluster_features: dict[str, np.ndarray] = {"velocity": velocity, "energy": energy}
        cluster_features.update(local_features)
        cluster_labels = self.cluster_states(embedded, cluster_features)
        label_features = dict(cluster_features)
        if system_type:
            label_features["system_type"] = np.array([system_type], dtype=object)
        label_names = self.label_sequence(series, cluster_labels, embedded, label_features)
        if smooth_labels:
            label_names = self._smooth_labels(label_names, min_run=min_run)

        summary_rows = self._build_summary(
            embedded, velocity, energy, label_names, extra_features=local_features
        )
        run_id = _compute_run_id(
            system_type=system_type,
            method=self.method,
            tau=self.tau,
            m=self.m,
            n_samples=int(embedded.shape[0]),
            filename_suffix=filename_suffix,
        )
        context = _build_context(
            run_id=run_id,
            system_type=system_type,
            method=self.method,
            tau=self.tau,
            m=self.m,
            n_samples=int(embedded.shape[0]),
            dates=dates,
            filename_suffix=filename_suffix,
        )
        summary_rows_std = _standardize_summary(summary_rows, label_names, context)
        summary_path = output_path / f"summary{filename_suffix}.csv"
        self._write_csv(summary_path, summary_rows_std)

        debug_path = output_path / f"debug_entropy{filename_suffix}.csv"
        self._write_csv(debug_path, metrics)

        report_path = output_path / f"report{filename_suffix}.md"
        macro_notes: list[dict[str, str]] = []
        if dates is not None and macro_events_path:
            start = (self.m - 1) * self.tau
            dates_aligned = np.asarray(dates)[start : start + embedded.shape[0]]
            events = load_macro_events(Path(macro_events_path))
            macro_notes = annotate_transitions(
                dates_aligned,
                label_names,
                events,
                asset=macro_asset,
                window_days=macro_window_days,
            )
        confidence = _compute_confidence(
            embedded=embedded,
            labels=label_names,
            cluster_labels=cluster_labels,
            metrics=metrics,
            current_label=str(label_names[-1]) if label_names.size else "",
        )
        warnings_list = confidence.get("warnings", [])
        if write_meta:
            meta_path = output_path / f"meta{filename_suffix}.json"
            _write_meta(meta_path, context, warnings_list)
        if write_confidence:
            breakdown_path = output_path / f"confidence_breakdown{filename_suffix}.csv"
            _write_breakdown(breakdown_path, confidence)
            verdict_path = output_path / f"verdict{filename_suffix}.json"
            _write_verdict(verdict_path, confidence)

        master_plot_path = ""
        if write_master_plot and plt is not None:
            master_plot_path = _plot_master(
                output_path,
                series,
                embedded,
                velocity,
                label_names,
                confidence,
                filename_suffix=filename_suffix,
            )

        if generate_report:
            self._write_report(
                report_path,
                best_m=best_m,
                best_tau=best_tau,
                selection_criterion=selection_criterion,
                metrics=metrics,
                summary=summary_rows_std,
                system_type=system_type,
                filename_suffix=filename_suffix,
                macro_notes=macro_notes,
                verdict=confidence,
                master_plot=master_plot_path,
            )

        plot_paths = {}
        if generate_plots:
            plot_paths = self._generate_plots(
                output_path,
                series,
                embedded,
                velocity,
                energy,
                label_names,
                metrics,
                filename_suffix=filename_suffix,
            )

        return {
            "best_m": best_m,
            "best_tau": best_tau,
            "summary_csv": str(summary_path),
            "debug_entropy_csv": str(debug_path),
            "report_md": str(report_path) if generate_report else "",
            "meta_json": str(output_path / f"meta{filename_suffix}.json") if write_meta else "",
            "confidence_csv": str(output_path / f"confidence_breakdown{filename_suffix}.csv")
            if write_confidence
            else "",
            "verdict_json": str(output_path / f"verdict{filename_suffix}.json") if write_confidence else "",
            "master_plot": master_plot_path,
            "plots": plot_paths,
            "cluster_labels": cluster_labels,
            "label_names": label_names,
        }

    def _build_summary(
        self,
        embedded: np.ndarray,
        velocity: np.ndarray,
        energy: np.ndarray,
        label_names: np.ndarray,
        extra_features: dict[str, np.ndarray] | None = None,
    ) -> list[dict[str, float | str]]:
        """Resume estatísticas por regime para gerar summary.csv.

        Args:
            embedded: Matriz do embedding.
            velocity: Vetor de velocidade alinhado.
            energy: Vetor de energia alinhado.
            label_names: Vetor de rótulos por amostra.

        Returns:
            Lista de dicionários com estatísticas por regime.
        """
        labels = np.asarray(label_names)
        unique, counts = np.unique(labels, return_counts=True)
        total = labels.size
        transitions_out: dict[str, int] = {}
        segments_count: dict[str, int] = {}
        if labels.size > 1:
            changes = labels[1:] != labels[:-1]
            for idx, changed in enumerate(changes, start=1):
                if changed:
                    prev_label = str(labels[idx - 1])
                    transitions_out[prev_label] = transitions_out.get(prev_label, 0) + 1
        # Conta segmentos contínuos por regime
        if labels.size > 0:
            current = str(labels[0])
            segments_count[current] = segments_count.get(current, 0) + 1
            for value in labels[1:]:
                value_str = str(value)
                if value_str != current:
                    current = value_str
                    segments_count[current] = segments_count.get(current, 0) + 1
        summary: list[dict[str, float | str]] = []
        for regime, count in zip(unique, counts):
            mask = labels == regime
            row: dict[str, float | str] = {
                "regime": str(regime),
                "count": float(count),
                "percent": float(count / total * 100.0),
                "mean_x": float(np.nanmean(embedded[mask, 0])),
                "std_x": float(np.nanstd(embedded[mask, 0])),
                "abs_mean_x": float(np.nanmean(np.abs(embedded[mask, 0]))),
                "mean_v": float(np.nanmean(velocity[mask])),
                "std_v": float(np.nanstd(velocity[mask])),
                "abs_mean_v": float(np.nanmean(np.abs(velocity[mask]))),
                "mean_energy": float(np.nanmean(energy[mask])),
                "std_energy": float(np.nanstd(energy[mask])),
                "energy_p10": float(np.nanpercentile(energy[mask], 10)),
                "energy_p90": float(np.nanpercentile(energy[mask], 90)),
                "transitions_out": float(transitions_out.get(str(regime), 0)),
                "segments": float(segments_count.get(str(regime), 0)),
            }
            if extra_features:
                for name, values in extra_features.items():
                    if values.shape[0] == labels.shape[0]:
                        row[f"mean_{name}"] = float(np.nanmean(values[mask]))
                        row[f"std_{name}"] = float(np.nanstd(values[mask]))
            summary.append(row)
        return summary

    def _write_csv(self, path: Path, rows: list[dict[str, float | str]]) -> None:
        """Escreve uma lista de dicionários em CSV.

        Args:
            path: Caminho do arquivo CSV.
            rows: Linhas a serem escritas.
        """
        if not rows:
            return
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)

    def _write_report(
        self,
        path: Path,
        best_m: int,
        best_tau: int,
        selection_criterion: str,
        metrics: list[dict[str, float]],
        summary: list[dict[str, float | str]],
        system_type: str | None,
        filename_suffix: str = "",
        macro_notes: list[dict[str, str]] | None = None,
        verdict: dict[str, object] | None = None,
        master_plot: str = "",
    ) -> None:
        """Gera um relatório em Markdown explicando os regimes detectados.

        Args:
            path: Caminho do relatório Markdown.
            best_m: Melhor dimensão selecionada.
            best_tau: Melhor atraso selecionado.
            selection_criterion: Critério usado na seleção.
            metrics: Lista com métricas de entropia e recorrência.
            summary: Lista com estatísticas por regime.
            system_type: Tipo do sistema, se informado.
        """
        lines = [
            "# Relatório de Regimes",
            "",
            f"- Sistema: {system_type or 'desconhecido'}",
            f"- Melhor (m, τ): ({best_m}, {best_tau})",
            f"- Critério de seleção: {selection_criterion}",
            "",
            "## Resumo por regime",
        ]
        for row in summary:
            label = row.get("label", row.get("regime", ""))
            pct = row.get("pct_time", row.get("percent", 0.0))
            energy = row.get("energy_mean", row.get("mean_energy", 0.0))
            mean_x = row.get("mean_x", 0.0)
            mean_v = row.get("mean_v", 0.0)
            lines.append(
                f"- {label}: {float(pct):.2f}% | "
                f"energia média {float(energy):.4f} | "
                f"média x {float(mean_x):.4f} | média v {float(mean_v):.4f}"
            )
        lines.extend(
            [
                "",
                "## Arquivos gerados",
                f"- master_plot{filename_suffix}.png" if master_plot else "",
                f"- regime_map{filename_suffix}.png",
                f"- labels_over_time{filename_suffix}.png",
                f"- xv_regime{filename_suffix}.png",
                f"- recurrence_plot{filename_suffix}.png",
                f"- entropy_vs_tau{filename_suffix}.png",
                f"- regime_3d{filename_suffix}.png (se disponível)",
                f"- summary{filename_suffix}.csv",
                f"- debug_entropy{filename_suffix}.csv",
                "",
                "## Observações",
                "Entropia e recorrência foram calculadas a partir do embedding discretizado.",
                "Para sistemas desconhecidos, rótulos genéricos são utilizados.",
            ]
        )
        if verdict:
            lines.extend(
                [
                    "",
                    "## Veredito",
                    f"- verdict: {verdict.get('verdict', '')}",
                    f"- confidence_level: {verdict.get('level', '')}",
                    f"- score: {verdict.get('score', '')}",
                    f"- action: {verdict.get('action', '')}",
                    f"- recommended_horizon: {verdict.get('recommended_horizon', '')}",
                ]
            )
        if macro_notes:
            lines.extend(
                [
                    "",
                    "## Anotações macro (próximas a transições)",
                ]
            )
            for note in macro_notes[:20]:
                lines.append(
                    f"- {note['date']}: {note['from']} → {note['to']} | {note['asset']} "
                    f"({note['range']} {note['variation']}) — {note['description']}"
                )
        path.write_text("\n".join(lines), encoding="utf-8")

    def _generate_plots(
        self,
        output_path: Path,
        series: np.ndarray,
        embedded: np.ndarray,
        velocity: np.ndarray,
        energy: np.ndarray,
        label_names: np.ndarray,
        metrics: list[dict[str, float]],
        filename_suffix: str = "",
    ) -> dict[str, str]:
        """Gera gráficos principais e retorna os caminhos.

        Args:
            output_path: Pasta de saída para os gráficos.
            series: Série temporal original.
            embedded: Matriz do embedding.
            velocity: Vetor de velocidade alinhado.
            energy: Vetor de energia alinhado.
            label_names: Rótulos por amostra.
            metrics: Métricas de entropia e recorrência por (m, τ).

        Returns:
            Dicionário com os caminhos dos gráficos gerados.
        """
        if plt is None:
            return {}

        plot_paths: dict[str, str] = {}
        labels = np.asarray(label_names)
        unique_labels = np.unique(labels)
        cmap = plt.get_cmap("tab10")
        color_map = {lab: cmap(i % 10) for i, lab in enumerate(unique_labels)}

        # Espaço embutido colorido por cluster (2D)
        if embedded.shape[1] >= 2:
            fig, ax = plt.subplots(figsize=(7, 5))
            for lab in unique_labels:
                mask = labels == lab
                ax.scatter(
                    embedded[mask, 0],
                    embedded[mask, 1],
                    s=8,
                    alpha=0.75,
                    label=str(lab),
                    color=color_map[lab],
                )
            ax.set_xlabel("x(t)")
            ax.set_ylabel(f"x(t-{self.tau})")
            ax.set_title("Regime map (embedding)")
            ax.legend(markerscale=2, fontsize=8)
            fig.tight_layout()
            out_path = output_path / f"regime_map{filename_suffix}.png"
            fig.savefig(out_path, dpi=150)
            plt.close(fig)
            plot_paths["regime_map"] = str(out_path)

        # Série temporal com rótulos
        start = (self.m - 1) * self.tau
        time_idx = np.arange(start, start + embedded.shape[0])
        fig, ax = plt.subplots(figsize=(9, 4))
        ax.plot(time_idx, np.asarray(series)[start : start + embedded.shape[0]], color="#64748b")
        for lab in unique_labels:
            mask = labels == lab
            ax.scatter(time_idx[mask], np.asarray(series)[start : start + embedded.shape[0]][mask], s=10, color=color_map[lab], label=str(lab))
        ax.set_xlabel("t")
        ax.set_ylabel("x(t)")
        ax.set_title("Labels ao longo do tempo")
        ax.legend(markerscale=1.5, fontsize=8)
        fig.tight_layout()
        out_path = output_path / f"labels_over_time{filename_suffix}.png"
        fig.savefig(out_path, dpi=150)
        plt.close(fig)
        plot_paths["labels_over_time"] = str(out_path)

        # Gráfico x0 vs v0
        fig, ax = plt.subplots(figsize=(7, 5))
        for lab in unique_labels:
            mask = labels == lab
            ax.scatter(
                embedded[mask, 0],
                velocity[mask],
                s=8,
                alpha=0.75,
                label=str(lab),
                color=color_map[lab],
            )
        ax.set_xlabel("x(t)")
        ax.set_ylabel("v(t)")
        ax.set_title("Espaço x(t) x v(t)")
        ax.legend(markerscale=2, fontsize=8)
        fig.tight_layout()
        out_path = output_path / f"xv_regime{filename_suffix}.png"
        fig.savefig(out_path, dpi=150)
        plt.close(fig)
        plot_paths["xv_regime"] = str(out_path)

        # Curva de entropia vs tau por m
        fig, ax = plt.subplots(figsize=(7, 4))
        metrics_by_m: dict[int, list[dict[str, float]]] = {}
        for row in metrics:
            metrics_by_m.setdefault(int(row["m"]), []).append(row)
        for m, rows in metrics_by_m.items():
            rows_sorted = sorted(rows, key=lambda r: r["tau"])
            taus = [r["tau"] for r in rows_sorted]
            entropies = [r["entropy"] for r in rows_sorted]
            ax.plot(taus, entropies, marker="o", label=f"m={m}")
        ax.set_xlabel("τ")
        ax.set_ylabel("Entropia")
        ax.set_title("Entropia vs τ")
        ax.legend(fontsize=8)
        fig.tight_layout()
        out_path = output_path / f"entropy_vs_tau{filename_suffix}.png"
        fig.savefig(out_path, dpi=150)
        plt.close(fig)
        plot_paths["entropy_vs_tau"] = str(out_path)

        # Recurrence plot
        sample = embedded
        if sample.shape[0] > 600:
            idx = np.random.default_rng(42).choice(sample.shape[0], size=600, replace=False)
            sample = sample[idx]
        diffs = sample[:, None, :] - sample[None, :, :]
        dists = np.linalg.norm(diffs, axis=2)
        tri = dists[np.triu_indices(dists.shape[0], k=1)]
        eps = np.percentile(tri, 10.0) if tri.size else 0.0
        rec = (dists <= eps).astype(float)
        fig, ax = plt.subplots(figsize=(5, 5))
        ax.imshow(rec, cmap="Greys", origin="lower")
        ax.set_title("Recurrence plot")
        ax.set_xlabel("t")
        ax.set_ylabel("t")
        fig.tight_layout()
        out_path = output_path / f"recurrence_plot{filename_suffix}.png"
        fig.savefig(out_path, dpi=150)
        plt.close(fig)
        plot_paths["recurrence_plot"] = str(out_path)

        # Gráfico 3D se possível: x, v, energia
        try:
            from mpl_toolkits.mplot3d import Axes3D  # noqa: F401

            fig = plt.figure(figsize=(7, 5))
            ax = fig.add_subplot(111, projection="3d")
            for lab in unique_labels:
                mask = labels == lab
                ax.scatter(
                    embedded[mask, 0],
                    velocity[mask],
                    energy[mask],
                    s=8,
                    alpha=0.7,
                    label=str(lab),
                    color=color_map[lab],
                )
            ax.set_xlabel("x(t)")
            ax.set_ylabel("v(t)")
            ax.set_zlabel("E(t)")
            ax.set_title("Separação de regimes (3D)")
            ax.legend(markerscale=2, fontsize=8)
            fig.tight_layout()
            out_path = output_path / f"regime_3d{filename_suffix}.png"
            fig.savefig(out_path, dpi=150)
            plt.close(fig)
            plot_paths["regime_3d"] = str(out_path)
        except Exception:
            pass

        return plot_paths


def _compute_run_id(**kwargs) -> str:
    payload = json.dumps(kwargs, sort_keys=True, default=str)
    return hashlib.sha1(payload.encode("utf-8")).hexdigest()[:12]


def _build_context(
    run_id: str,
    system_type: str | None,
    method: str,
    tau: int,
    m: int,
    n_samples: int,
    dates: np.ndarray | None,
    filename_suffix: str,
) -> dict[str, object]:
    dt = None
    if dates is not None and len(dates) > 1:
        try:
            diffs = np.diff(np.asarray(dates).astype("datetime64[ns]"))
            dt = float(np.median(diffs.astype("timedelta64[s]").astype(float)))
        except Exception:
            dt = None
    return {
        "run_id": run_id,
        "system_type": system_type or "",
        "method": method,
        "tau": int(tau),
        "m": int(m),
        "n_samples": int(n_samples),
        "dt_seconds": dt,
        "filename_suffix": filename_suffix,
    }


def _standardize_summary(
    rows: list[dict[str, float | str]],
    labels: np.ndarray,
    context: dict[str, object],
) -> list[dict[str, float | str]]:
    out: list[dict[str, float | str]] = []
    for row in rows:
        label = str(row.get("regime", ""))
        count = float(row.get("count", 0.0))
        pct = float(row.get("percent", 0.0))
        base = {
            "run_id": context.get("run_id", ""),
            "entity_name": "",
            "system_type": context.get("system_type", ""),
            "ticker": "",
            "freq": "",
            "method": context.get("method", ""),
            "n_samples": context.get("n_samples", ""),
            "dt": context.get("dt_seconds", ""),
            "m": context.get("m", ""),
            "tau": context.get("tau", ""),
            "cluster_id": "",
            "label": label,
            "pct_time": pct,
            "n_segments": float(row.get("segments", 0.0)),
            "mean_duration": "",
            "std_duration": "",
            "energy_mean": float(row.get("mean_energy", np.nan)),
            "energy_std": float(row.get("std_energy", np.nan)),
            "entropy_mean": float(row.get("mean_local_entropy", np.nan)),
            "recurrence_mean": float(row.get("mean_local_rr", np.nan)),
            "notes": "",
        }
        base.update(row)
        out.append(base)
    return out


def _compute_confidence(
    embedded: np.ndarray,
    labels: np.ndarray,
    cluster_labels: np.ndarray,
    metrics: list[dict[str, float]],
    current_label: str,
) -> dict[str, object]:
    warnings_list: list[str] = []
    n = len(labels)
    if n == 0:
        return {
            "score": 0.0,
            "level": "LOW",
            "action": "NAO_OPERAR",
            "recommended_horizon": "curto",
            "warnings": ["SEM_DADOS"],
            "breakdown": [],
            "verdict": "NAO",
        }

    unique_labels = np.unique(labels)
    n_clusters = len(unique_labels)
    if n_clusters == 1:
        warnings_list.append("COLAPSO_CLUSTER")
    if n_clusters > 10:
        warnings_list.append("OVERCLUSTER")
    if current_label.startswith("state_") or not current_label:
        warnings_list.append("SEM_ROTULO")

    # transition rate (last 10%)
    window = max(10, int(0.1 * n))
    recent = labels[-window:]
    changes = np.sum(recent[1:] != recent[:-1])
    transition_rate = float(changes / max(1, (len(recent) - 1)))
    if transition_rate > 0.3:
        warnings_list.append("REGIME_INSTAVEL")

    # regime purity
    current_pct = float(np.mean(recent == recent[-1])) if recent.size else 0.0

    # cluster stability proxy
    stability = 0.0
    if embedded.size and n_clusters > 1:
        centroids = []
        for lab in unique_labels:
            centroids.append(np.nanmean(embedded[labels == lab], axis=0))
        centroids = np.array(centroids)
        inter = np.mean(
            np.linalg.norm(centroids[:, None, :] - centroids[None, :, :], axis=2)
        )
        intra = 0.0
        for lab in unique_labels:
            pts = embedded[labels == lab]
            if pts.size == 0:
                continue
            c = np.nanmean(pts, axis=0)
            intra += float(np.mean(np.linalg.norm(pts - c, axis=1)))
        intra = intra / max(1, n_clusters)
        ratio = intra / max(inter, 1e-6)
        stability = float(np.clip(1.0 - ratio, 0.0, 1.0))

    # novelty (z-score distance from current cluster centroid)
    novelty = 0.0
    if embedded.size:
        current_cluster = cluster_labels[-1]
        pts = embedded[cluster_labels == current_cluster]
        if pts.size:
            c = np.nanmean(pts, axis=0)
            dists = np.linalg.norm(pts - c, axis=1)
            last_dist = float(np.linalg.norm(embedded[-1] - c))
            if np.std(dists) > 0:
                z = (last_dist - float(np.mean(dists))) / float(np.std(dists))
                novelty = float(np.clip(z / 3.0, 0.0, 1.0))
            else:
                novelty = 0.0
        if novelty > 0.7:
            warnings_list.append("FORA_DISTRIBUICAO")

    # embedding quality proxy
    embedding_quality = 0.0
    if metrics:
        row = min(metrics, key=lambda x: abs(x.get("m", 0) - 0) + abs(x.get("tau", 0) - 0))
        rr = float(row.get("recurrence_rate", 0.0))
        embedding_quality = float(np.clip((rr - 0.01) / 0.2, 0.0, 1.0))
    if embedding_quality < 0.3:
        warnings_list.append("EMBEDDING_FRACO")

    weights = {
        "cluster_stability": 0.3,
        "novelty": 0.2,
        "transition_rate": 0.2,
        "regime_purity": 0.15,
        "embedding_quality": 0.15,
        "method_agreement": 0.0,
    }
    breakdown = []
    def add_metric(name, raw, norm, weight, comment):
        breakdown.append(
            {
                "metric_name": name,
                "raw_value": raw,
                "normalized_value": norm,
                "weight": weight,
                "contribution": norm * weight,
                "comment": comment,
            }
        )

    add_metric("cluster_stability", stability, stability, weights["cluster_stability"], "proxy intra/inter")
    add_metric("novelty", novelty, 1.0 - novelty, weights["novelty"], "fora de distribuicao penaliza")
    add_metric("transition_rate", transition_rate, 1.0 - transition_rate, weights["transition_rate"], "mudancas recentes")
    add_metric("regime_purity", current_pct, current_pct, weights["regime_purity"], "dominancia do regime atual")
    add_metric("embedding_quality", embedding_quality, embedding_quality, weights["embedding_quality"], "recorrencia/entropia proxy")
    add_metric("method_agreement", 0.0, 0.0, weights["method_agreement"], "nao aplicado")

    score = float(np.clip(sum(item["contribution"] for item in breakdown) * 100.0, 0.0, 100.0))
    if score >= 70:
        level = "HIGH"
        action = "OPERAR"
        verdict = "SIM"
        recommended_horizon = "medio"
    elif score >= 50:
        level = "MED"
        action = "REDUZIR_RISCO"
        verdict = "DEPENDE"
        recommended_horizon = "curto"
    else:
        level = "LOW"
        action = "NAO_OPERAR"
        verdict = "NAO"
        recommended_horizon = "curto"

    return {
        "score": round(score, 2),
        "level": level,
        "action": action,
        "recommended_horizon": recommended_horizon,
        "warnings": warnings_list,
        "breakdown": breakdown,
        "verdict": verdict,
    }


def _write_meta(path: Path, context: dict[str, object], warnings_list: list[str]) -> None:
    payload = dict(context)
    payload["warnings"] = warnings_list
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _write_breakdown(path: Path, confidence: dict[str, object]) -> None:
    rows = confidence.get("breakdown", [])
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _write_verdict(path: Path, confidence: dict[str, object]) -> None:
    payload = {k: v for k, v in confidence.items() if k != "breakdown"}
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _plot_master(
    output_path: Path,
    series: np.ndarray,
    embedded: np.ndarray,
    velocity: np.ndarray,
    label_names: np.ndarray,
    confidence: dict[str, object],
    filename_suffix: str = "",
) -> str:
    if plt is None:
        return ""
    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    labels = np.asarray(label_names)
    unique_labels = np.unique(labels)
    cmap = plt.get_cmap("tab10")
    color_map = {lab: cmap(i % 10) for i, lab in enumerate(unique_labels)}

    # time series
    ax = axes[0, 0]
    offset = max(0, len(series) - len(labels))
    series_aligned = np.asarray(series)[offset : offset + len(labels)]
    ax.plot(series_aligned, color="#64748b", linewidth=1.0)
    for lab in unique_labels:
        mask = labels == lab
        ax.scatter(
            np.where(mask)[0],
            series_aligned[mask],
            s=6,
            color=color_map[lab],
            label=str(lab),
        )
    ax.set_title("Serie + regimes")

    # embedding scatter
    ax = axes[0, 1]
    if embedded.shape[1] >= 2:
        for lab in unique_labels:
            mask = labels == lab
            ax.scatter(embedded[mask, 0], embedded[mask, 1], s=6, color=color_map[lab])
        ax.set_title("Embedding (2D)")
    else:
        ax.text(0.5, 0.5, "Embedding insuficiente", ha="center")

    # phase portrait
    ax = axes[1, 0]
    ax.scatter(embedded[:, 0], velocity, s=6, color="#0f172a", alpha=0.6)
    ax.set_title("Retrato de fase (x vs v)")

    # text box
    ax = axes[1, 1]
    ax.axis("off")
    text = (
        f"regime_atual: {labels[-1] if labels.size else ''}\n"
        f"score: {confidence.get('score')}\n"
        f"nivel: {confidence.get('level')}\n"
        f"action: {confidence.get('action')}\n"
        f"warnings: {', '.join(confidence.get('warnings', []))}"
    )
    ax.text(0.02, 0.98, text, va="top", fontsize=10)

    fig.tight_layout()
    out_path = output_path / f"master_plot{filename_suffix}.png"
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    return str(out_path)
