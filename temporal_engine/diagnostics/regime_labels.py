"""Regime detection labels and clustering utilities."""

from __future__ import annotations

from pathlib import Path
import csv

import numpy as np
from sklearn.cluster import DBSCAN, KMeans
from sklearn.preprocessing import StandardScaler

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
        if method == "hdbscan":
            if HDBSCAN is None:
                model = DBSCAN(**_filter_params({"eps", "min_samples", "metric", "p", "algorithm", "leaf_size"}))
                return model.fit_predict(scaled)
            model = HDBSCAN(**self.params)
            return model.fit_predict(scaled)
        if method == "dbscan":
            model = DBSCAN(**_filter_params({"eps", "min_samples", "metric", "p", "algorithm", "leaf_size"}))
            return model.fit_predict(scaled)
        if method == "kmeans":
            model = KMeans(**_filter_params({"n_clusters", "random_state", "n_init", "max_iter", "tol", "algorithm"}))
            return model.fit_predict(scaled)

        raise ValueError(f"Unknown clustering method: {self.method}")

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
            cluster_stats[int(label)] = {
                "mean_x": mean_x,
                "mean_energy": mean_e,
                "mean_velocity": v_mean,
                "std_velocity": v_std,
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
                if high_energy or count == min_count:
                    cluster_name_map[int(label)] = "transicao"
                elif mean_x < 0:
                    cluster_name_map[int(label)] = "poco_esquerdo"
                else:
                    cluster_name_map[int(label)] = "poco_direito"

        self.last_cluster_stats = cluster_stats
        return np.array([cluster_name_map[int(lbl)] for lbl in labels], dtype=object)

    def run_full_analysis(
        self,
        series: np.ndarray,
        output_dir: str | Path,
        system_type: str | None = None,
        filename_suffix: str = "",
        tau_range: range = range(1, 11),
        m_range: range = range(2, 6),
        selection_criterion: str = "min_entropy",
        bins: int = 10,
        rr_percentile: float = 10.0,
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
        cluster_features: dict[str, np.ndarray] = {"velocity": velocity, "energy": energy}
        cluster_labels = self.cluster_states(embedded, cluster_features)
        label_features = dict(cluster_features)
        if system_type:
            label_features["system_type"] = np.array([system_type], dtype=object)
        label_names = self.label_sequence(series, cluster_labels, embedded, label_features)

        summary_rows = self._build_summary(embedded, velocity, energy, label_names)
        summary_path = output_path / f"summary{filename_suffix}.csv"
        self._write_csv(summary_path, summary_rows)

        debug_path = output_path / f"debug_entropy{filename_suffix}.csv"
        self._write_csv(debug_path, metrics)

        report_path = output_path / f"report{filename_suffix}.md"
        self._write_report(
            report_path,
            best_m=best_m,
            best_tau=best_tau,
            selection_criterion=selection_criterion,
            metrics=metrics,
            summary=summary_rows,
            system_type=system_type,
            filename_suffix=filename_suffix,
        )

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
            "report_md": str(report_path),
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
        if labels.size > 1:
            changes = labels[1:] != labels[:-1]
            for idx, changed in enumerate(changes, start=1):
                if changed:
                    prev_label = str(labels[idx - 1])
                    transitions_out[prev_label] = transitions_out.get(prev_label, 0) + 1
        summary: list[dict[str, float | str]] = []
        for regime, count in zip(unique, counts):
            mask = labels == regime
            summary.append(
                {
                    "regime": str(regime),
                    "count": float(count),
                    "percent": float(count / total * 100.0),
                    "mean_x": float(np.nanmean(embedded[mask, 0])),
                    "std_x": float(np.nanstd(embedded[mask, 0])),
                    "mean_v": float(np.nanmean(velocity[mask])),
                    "std_v": float(np.nanstd(velocity[mask])),
                    "mean_energy": float(np.nanmean(energy[mask])),
                    "std_energy": float(np.nanstd(energy[mask])),
                    "transitions_out": float(transitions_out.get(str(regime), 0)),
                }
            )
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
            lines.append(
                f"- {row['regime']}: {row['percent']:.2f}% | "
                f"energia média {row['mean_energy']:.4f} | "
                f"média x {row['mean_x']:.4f} | média v {row['mean_v']:.4f}"
            )
        lines.extend(
            [
                "",
                "## Arquivos gerados",
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
        eps = np.percentile(dists[np.triu_indices(dists.shape[0], k=1)], 10.0)
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
