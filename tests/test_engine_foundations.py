from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.api_records import PredictionRecord, save_prediction_records
from engine.finance_utils import (
    FinancialDatasetSpec,
    compute_confidence_finance,
    compute_metrics,
    prepare_financial_series,
    standardize_train_test,
)
from engine.forecast import forecast_series
from engine.io import load_dataset
from engine.preprocess import preprocess
from engine.sanity import safe_test_indices, validate_time_split
from engine.temporal import TemporalConfig, YearResult, evaluate_years, select_best_horizon
from engine.validation_gate import evaluate_gate
from engine.features.phase_features import compute_phase_features


def test_api_records_write_jsonl_and_csv(tmp_path: Path) -> None:
    rec = PredictionRecord(timestamp="2026-02-11T00:00:00Z", asset="SPY", timeframe="daily", warnings=["w1"])
    jsonl = tmp_path / "records.jsonl"
    csv = tmp_path / "records.csv"
    save_prediction_records([rec], jsonl, csv)
    lines = jsonl.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    payload = json.loads(lines[0])
    assert payload["asset"] == "SPY"
    assert payload["warnings"] == ["w1"]
    assert csv.exists()


def test_load_dataset_reads_and_coerces_types(tmp_path: Path) -> None:
    path = tmp_path / "input.csv"
    path.write_text("ts,val\n2026-01-01,10\n2026-01-02,12\n", encoding="utf-8")
    df, tcol, vcol = load_dataset(path, "ts", "val")
    assert tcol == "ts"
    assert vcol == "val"
    assert pd.api.types.is_datetime64_any_dtype(df["ts"])
    assert pd.api.types.is_numeric_dtype(df["val"])


def test_forecast_series_supports_mean_and_trend() -> None:
    times = pd.date_range("2026-01-01", periods=10, freq="D")
    values = np.linspace(100.0, 109.0, 10)
    df = pd.DataFrame({"time": times, "value": values})
    fc_mean, msg = forecast_series(df, "time", "value", horizon=3, method="media_recente", dt_seconds=86400.0)
    assert len(fc_mean) == 3
    assert "Previsao simples" in msg
    fc_trend, _ = forecast_series(df, "time", "value", horizon=3, method="tendencia_curta", dt_seconds=86400.0)
    assert fc_trend["value_previsto"].iloc[-1] > fc_trend["value_previsto"].iloc[0]


def test_validation_gate_respects_thresholds() -> None:
    cfg = {
        "default": {"min_quality": 0.5, "min_confidence": 0.5},
        "domains": {"finance": {"max_transition_rate": 0.4, "max_novelty": 0.8}},
    }
    ok = evaluate_gate(asset="SPY", quality=0.8, confidence=0.8, transition_rate=0.2, novelty=0.2, config=cfg)
    assert ok.status == "validated"
    bad = evaluate_gate(asset="SPY", quality=0.3, confidence=0.4, transition_rate=0.7, novelty=0.9, config=cfg)
    assert bad.status == "inconclusive"
    assert "quality_below_gate" in bad.reasons


def test_sanity_validate_split_and_safe_indices() -> None:
    dates = pd.date_range("2026-01-01", periods=6, freq="D")
    train_mask = np.array([1, 1, 1, 0, 0, 0], dtype=bool)
    test_mask = ~train_mask
    validate_time_split(dates, train_mask, test_mask, train_end=pd.Timestamp("2026-01-03"))
    safe, dropped = safe_test_indices(test_mask, min_valid_index=4)
    np.testing.assert_array_equal(safe, np.array([4, 5]))
    assert dropped == 1


def test_finance_prepare_metrics_and_confidence() -> None:
    df = pd.DataFrame(
        {
            "date": pd.date_range("2026-01-01", periods=20, freq="D"),
            "close": np.linspace(100.0, 110.0, 20),
        }
    )
    spec = FinancialDatasetSpec(entity_name="SPY", freq="daily", price_col="close", target_type="log_return")
    prepared, meta = prepare_financial_series(df, spec)
    assert set(prepared.columns) == {"date", "y", "y_raw"}
    assert meta["entity_name"] == "SPY"

    split = len(prepared) // 2
    train = prepared.iloc[:split].copy()
    test = prepared.iloc[split:].copy()
    train_std, test_std, stats = standardize_train_test(train, test)
    assert "mean" in stats and "std" in stats

    y_true_raw = test["y_raw"].to_numpy()
    y_pred_raw = y_true_raw * 0.9
    naive = y_true_raw * 0.8
    metrics = compute_metrics(y_true_raw, y_pred_raw, test_std["y"].to_numpy(), test_std["y"].to_numpy() * 0.9, naive, "log_return")
    assert "mase" in metrics
    confidence = compute_confidence_finance(metrics, error_std=0.2, transition_rate=0.1, novelty=0.2)
    assert confidence["level"] in {"HIGH", "MED", "LOW"}
    assert "score" in confidence


def test_sanity_raises_on_overlap() -> None:
    dates = pd.date_range("2026-01-01", periods=4, freq="D")
    train_mask = np.array([1, 1, 0, 0], dtype=bool)
    test_mask = np.array([0, 1, 1, 0], dtype=bool)
    with pytest.raises(ValueError, match="sobreposicao"):
        validate_time_split(dates, train_mask, test_mask)


def test_preprocess_basic_path_without_ons() -> None:
    df = pd.DataFrame(
        {
            "time": pd.date_range("2026-01-01", periods=6, freq="D"),
            "value": [1.0, 1.1, 0.9, 1.2, np.nan, 1.0],
        }
    )
    out, meta, tcol, vcol = preprocess(
        df=df,
        time_col="time",
        value_col="value",
        source="custom",
        preencher=True,
        remover_repetidos=True,
    )
    assert tcol == "time"
    assert vcol == "value"
    assert len(out) >= 5
    assert meta["rows_out"] == len(out)


def test_report_region_key_inference() -> None:
    report = pytest.importorskip("engine.report")
    infer = report._infer_region_key
    assert infer("Norte") == "N"
    assert infer("Nordeste") == "NE"
    assert infer("Sudeste e Centro-Oeste") == "SE/CO"
    assert infer("Sul") == "S"


def test_temporal_engine_summary_and_horizon_choice() -> None:
    cfg = TemporalConfig(min_improvement_pct=0.02, required_win_rate=0.6, required_years_min=3)
    yearly = [
        YearResult(year=2021, model_error=0.90, baseline_error=1.00),
        YearResult(year=2022, model_error=0.85, baseline_error=1.00),
        YearResult(year=2023, model_error=1.05, baseline_error=1.00),
    ]
    summary = evaluate_years(yearly, cfg)
    assert summary.years == 3
    assert summary.status in {"SIM", "DEPENDE", "NAO"}

    horizons = {
        "h1": yearly,
        "h5": [
            YearResult(year=2021, model_error=0.99, baseline_error=1.00),
            YearResult(year=2022, model_error=1.01, baseline_error=1.00),
            YearResult(year=2023, model_error=0.98, baseline_error=1.00),
        ],
    }
    best_h, best_summary = select_best_horizon(horizons, cfg)
    assert best_h in {"h1", "h5"}
    assert best_summary.horizon == best_h


def test_phase_features_compute_dataframe() -> None:
    n = 400
    x = np.linspace(0, 16 * np.pi, n)
    series = np.sin(x) + 0.05 * np.cos(3 * x)
    dates = pd.date_range("2025-01-01", periods=n, freq="D")
    out = compute_phase_features(series, dates, tau=2, m=4, window=120, delta=1)
    assert out is not None
    assert len(out) > 0
    assert {"date", "raio_rms", "anisotropia", "drift_local", "divergence_rate", "autocorr"}.issubset(out.columns)
