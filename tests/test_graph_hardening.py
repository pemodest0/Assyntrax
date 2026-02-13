from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib
import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
matplotlib.use("Agg")

from engine.graph.export import write_asset_bundle
from engine.graph.graph_builder import build_micrograph, knn_edges, normalize_counts, transition_counts
from engine.graph.core import run_graph_engine
from engine.graph.labels import compute_graph_quality, labels_for_series
from engine.graph.merge_existing import merge_forecast_risk
from engine.graph.metastable import metastable_regimes
from engine.graph.microstates import build_microstates
from engine.graph.plots import plot_embedding_2d, plot_stretch_hist, plot_timeline_regime, plot_transition_matrix
from engine.graph.report import write_asset_report
from engine.graph.risk_thresholds import get_risk_thresholds, set_risk_thresholds
from engine.graph.sanity import sanity_alerts
from engine.graph.schema import GraphAsset, GraphConfig, GraphLinks, GraphMetrics, GraphState


def _sample_asset() -> GraphAsset:
    return GraphAsset(
        asset="SPY",
        timeframe="daily",
        asof="2026-02-11",
        state=GraphState(label="UNSTABLE", confidence=0.6),
        graph=GraphConfig(n_micro=4, k_nn=6, theiler=1, alpha=0.1),
        metrics=GraphMetrics(stay_prob=0.4, escape_prob=0.6, stretch_mu=0.1, stretch_frac_pos=0.55),
        alerts=[],
        links=GraphLinks(
            regimes_csv="assets/SPY_daily_regimes.csv",
            embedding_csv="assets/SPY_daily_embedding.csv",
            micrograph_json="assets/SPY_daily_micrograph.json",
            transitions_json="assets/SPY_daily_transitions.json",
        ),
    )


def test_write_asset_bundle_writes_expected_files(tmp_path: Path) -> None:
    asset = _sample_asset()
    embedding = np.array([[1.0, 2.0], [3.0, 4.0]])
    regimes = [{"date": "2026-02-11", "regime": "risk_off"}]

    write_asset_bundle(
        asset=asset,
        outdir=tmp_path,
        embedding=embedding,
        regimes=regimes,
        micrograph={"nodes": []},
        transitions={"edges": []},
    )

    base = tmp_path / "assets" / "SPY_daily"
    assert (base.with_suffix(".json")).exists()
    assert (tmp_path / "assets" / "SPY_daily_embedding.csv").exists()
    assert (tmp_path / "assets" / "SPY_daily_regimes.csv").exists()
    assert (tmp_path / "assets" / "SPY_daily_micrograph.json").exists()
    assert (tmp_path / "assets" / "SPY_daily_transitions.json").exists()


def test_get_risk_thresholds_returns_copy_and_fallback_multiplier() -> None:
    baseline = get_risk_thresholds("SPY", "daily")
    baseline["macro"] = 999.0
    fresh = get_risk_thresholds("SPY", "daily")
    assert fresh["macro"] != 999.0

    fallback = get_risk_thresholds("UNKNOWN", "daily", group="crypto")
    assert fallback["macro"] == pytest.approx(0.026)
    assert fallback["stress"] == pytest.approx(0.026)
    assert fallback["vol"] == pytest.approx(0.026)


def test_set_risk_thresholds_and_sanity_alerts() -> None:
    set_risk_thresholds("UNITTEST_X", "weekly", {"macro": 0.01, "stress": None, "vol": 0.03})
    custom = get_risk_thresholds("UNITTEST_X", "weekly")
    assert custom == {"macro": 0.01, "stress": None, "vol": 0.03}

    weekly_alerts = sanity_alerts(
        asset="SPY",
        n_micro=3,
        n_points=12,
        escape_prob=0.5,
        quality_score=0.9,
        timeframe="weekly",
    )
    daily_alerts = sanity_alerts(
        asset="SPY",
        n_micro=3,
        n_points=12,
        escape_prob=0.5,
        quality_score=0.9,
        timeframe="daily",
    )
    assert "TOO_MANY_MICROSTATES" not in weekly_alerts
    assert "TOO_MANY_MICROSTATES" in daily_alerts


def test_graph_builder_counts_and_micrograph_shape() -> None:
    labels = np.array([0, 1, 1, 0], dtype=int)
    counts = transition_counts(labels)
    np.testing.assert_allclose(counts, np.array([[0.0, 1.0], [1.0, 1.0]]))

    probs = normalize_counts(counts, alpha=0.0)
    np.testing.assert_allclose(probs.sum(axis=1), np.array([1.0, 1.0]))

    centroids = np.array([[0.0, 0.0], [1.0, 0.0], [0.0, 1.0]])
    edges = knn_edges(centroids, k=1)
    assert len(edges) == 3
    graph = build_micrograph(centroids, edges)
    assert len(graph["nodes"]) == 3
    assert len(graph["edges"]) == 3


def test_build_micrograph_accepts_1d_centroids() -> None:
    centroids = np.array([0.0, 1.0, 2.0], dtype=float)
    graph = build_micrograph(centroids, edges=[(0, 1), (1, 2)])
    assert len(graph["nodes"]) == 3
    assert graph["nodes"][0]["x"] == pytest.approx(0.0)
    assert graph["nodes"][0]["y"] == pytest.approx(0.0)
    assert len(graph["edges"]) == 2


def test_merge_forecast_risk_reads_latest_records_and_dashboard(tmp_path: Path) -> None:
    latest_dir = tmp_path / "latest"
    latest_dir.mkdir(parents=True)
    dashboard_dir = tmp_path / "dashboard"
    dashboard_dir.mkdir(parents=True)

    lines = [
        {
            "asset": "QQQ",
            "timeframe": "daily",
            "mase": 0.9,
            "dir_acc": 0.5,
            "alerts": [],
            "risk": {"level": "MEDIUM"},
        },
        {
            "asset": "SPY",
            "timeframe": "daily",
            "mase": 0.4,
            "dir_acc": 0.7,
            "alerts": ["A1"],
            "risk": {"level": "LOW"},
        },
    ]
    (latest_dir / "api_records.jsonl").write_text(
        "\n".join(json.dumps(row) for row in lines),
        encoding="utf-8",
    )
    (dashboard_dir / "overview.json").write_text(
        json.dumps({"assets": [{"asset": "SPY", "mean_confidence": 0.66}]}),
        encoding="utf-8",
    )

    merged = merge_forecast_risk(asset="SPY", timeframe="daily", outdir=tmp_path, base_results=tmp_path)
    assert merged["forecast_diag"]["mase"] == 0.4
    assert merged["forecast_diag"]["dir_acc"] == 0.7
    assert merged["forecast_diag"]["alerts"] == ["A1"]
    assert merged["forecast_diag"]["confidence_score"] == 0.66
    assert merged["risk"] == {"level": "LOW"}


def test_metastable_regimes_handles_edge_cases_and_pcca() -> None:
    empty = metastable_regimes(np.zeros((0, 0)), n_regimes=2)
    assert empty.size == 0

    trivial = metastable_regimes(np.array([[1.0, 0.0], [0.0, 1.0]]), n_regimes=1)
    np.testing.assert_array_equal(trivial, np.array([0, 0]))

    p = np.array([[0.9, 0.1], [0.2, 0.8]])
    labels = metastable_regimes(p, n_regimes=2, seed=3, method="pcca")
    assert labels.shape == (2,)
    assert set(labels.tolist()).issubset({0, 1})


def test_plot_helpers_emit_png_files(tmp_path: Path) -> None:
    regimes = np.array([0, 1, 1, 0, 2, 2], dtype=float)
    confidence = np.array([0.2, 0.5, 0.7, 0.4, 0.8, 0.6], dtype=float)
    matrix = np.array([[0.7, 0.3], [0.4, 0.6]], dtype=float)
    embedding = np.array([[0.0, 0.1], [1.0, 0.2], [0.8, 1.1]])
    stretch = np.array([0.1, 0.3, -0.2, 0.4, 0.0, 0.2])

    plot_timeline_regime(tmp_path, regimes, confidence)
    plot_transition_matrix(tmp_path, matrix)
    plot_embedding_2d(tmp_path, embedding, np.array([0, 1, 1]))
    plot_stretch_hist(tmp_path, stretch, np.array([0, 1, 1, 0, 1, 0]))

    assert (tmp_path / "timeline_regime.png").exists()
    assert (tmp_path / "transition_matrix.png").exists()
    assert (tmp_path / "embedding_2d.png").exists()
    assert (tmp_path / "stretch_hist.png").exists()


def test_microstates_kmeans_and_dbscan_paths() -> None:
    rng = np.random.default_rng(123)
    a = rng.normal(loc=(0.0, 0.0), scale=0.1, size=(20, 2))
    b = rng.normal(loc=(1.0, 1.0), scale=0.1, size=(20, 2))
    embedded = np.vstack([a, b])

    labels_k, centroids_k = build_microstates(embedded, n_micro=3, seed=7, method="kmeans")
    assert labels_k.shape == (40,)
    assert centroids_k.shape == (3, 2)

    labels_d, centroids_d = build_microstates(
        embedded,
        n_micro=3,
        seed=7,
        method="dbscan",
        cluster_params={"eps": 0.35, "min_samples": 3},
    )
    assert labels_d.shape == (40,)
    assert centroids_d.shape[1] == 2
    assert np.all(labels_d >= 0)


def test_labels_quality_and_series_output() -> None:
    n_nodes = 4
    edges = [(0, 1), (1, 2), (2, 3), (3, 0)]
    occupancy = np.array([10.0, 12.0, 9.0, 11.0])
    p = np.array(
        [
            [0.7, 0.2, 0.1, 0.0],
            [0.1, 0.7, 0.1, 0.1],
            [0.0, 0.2, 0.7, 0.1],
            [0.1, 0.0, 0.2, 0.7],
        ]
    )
    quality = compute_graph_quality(n_nodes, edges, occupancy, p, {"n_points": 40.0})
    assert 0.0 <= quality["score"] <= 1.0

    conf = np.array([0.85, 0.78, 0.40, 0.35, 0.70])
    stretch = np.array([0.05, 0.08, 0.20, 0.22, 0.10])
    frac_pos = np.array([0.1, 0.2, 0.8, 0.7, 0.3])
    states, thresholds = labels_for_series(conf, stretch, frac_pos, quality_score=quality["score"], timeframe="daily")
    assert states.shape == conf.shape
    assert set(states.tolist()).issubset({"STABLE", "TRANSITION", "UNSTABLE", "NOISY"})
    assert "escape_hi" in thresholds


def test_run_graph_engine_smoke_and_shapes() -> None:
    x = np.linspace(0, 12 * np.pi, 240)
    series = np.sin(x) + 0.05 * np.random.default_rng(321).normal(size=x.size)
    result = run_graph_engine(
        series=series,
        m=3,
        tau=1,
        n_micro=8,
        n_regimes=3,
        k_nn=2,
        theiler=3,
        alpha=1.0,
        seed=11,
        method="spectral",
        timeframe="daily",
    )
    n = result.embedding.shape[0]
    assert result.micro_labels.shape == (n,)
    assert result.confidence.shape == (n,)
    assert result.state_labels.shape == (n,)
    assert result.p_matrix.shape == (8, 8)
    assert set(result.state_labels.tolist()).issubset({"STABLE", "TRANSITION", "UNSTABLE", "NOISY"})


def test_report_writer_emits_markdown(tmp_path: Path) -> None:
    (tmp_path / "assets").mkdir(parents=True, exist_ok=True)
    path = write_asset_report(
        outdir=tmp_path,
        asset="SPY",
        timeframe="daily",
        state_label="TRANSITION",
        confidence=0.63,
        quality={"score": 0.6},
        metrics={"escape": 0.37},
        thresholds={"escape_hi": 0.4},
        graph_params={"n_micro": 8},
        recommendation="REDUZIR TAMANHO",
        gating={"forecast_reliable": True, "reasons": ["OK"]},
        diagnostics={"kappa": 0.2},
    )
    assert path.exists()
    text = path.read_text(encoding="utf-8")
    assert "Graph Regime Report" in text
    assert "SPY (daily)" in text
    assert "REDUZIR TAMANHO" in text
