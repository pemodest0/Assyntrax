from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.lab.run_corr_macro_offline import (
    _build_action_playbook,
    _build_era_evaluation,
    _build_operational_alerts,
    _build_ui_view_model,
)


def test_operational_alerts_emit_core_events() -> None:
    dates = pd.date_range("2020-03-10", periods=8, freq="D")
    ts_off = pd.DataFrame(
        {
            "date": dates.strftime("%Y-%m-%d"),
            "N_used": [50] * 8,
            "p1": [0.21, 0.85, 0.82, 0.55, 0.14, 0.13, 0.25, 0.52],
            "deff": [15.0, 3.0, 3.2, 7.0, 26.0, 27.0, 16.0, 8.5],
            "insufficient_universe": [False] * 8,
            "structure_score": [0.10, 0.30, 0.25, 0.05, 0.40, 0.35, 0.12, 0.08],
        }
    )
    regime_df = pd.DataFrame(
        {
            "date": dates.strftime("%Y-%m-%d"),
            "regime": ["stable", "stress", "stress", "transition", "dispersion", "dispersion", "stable", "transition"],
            "exposure": [0.7, 0.1, 0.1, 0.4, 0.9, 0.9, 0.7, 0.4],
            "dp1_5": [0.0, 0.3, 0.05, 0.7, -0.6, -0.1, 0.03, 0.8],
            "ddeff_5": [0.0, -2.0, -1.0, -6.0, 4.0, 1.0, 0.2, -5.5],
        }
    )
    robust = {"latest_joint_majority_5": 0.0, "joint_majority_60d": 0.2}

    events, payload, txt = _build_operational_alerts(ts_off=ts_off, regime_df=regime_df, robust_metrics=robust)

    assert not events.empty
    codes = set(events["event_code"].astype(str).tolist())
    assert "STRESS_ENTER" in codes
    assert "TRANSITION_SPIKE" in codes
    assert "REGIME_CHANGE" in codes
    assert "SIGNAL_UNCONFIRMED" in payload["latest_events"]
    assert "ROBUSTNESS_LOW" in payload["latest_events"]
    assert str(txt).startswith("operational_alerts_latest=")


def test_era_evaluation_and_playbook_contract() -> None:
    dates = pd.to_datetime(
        [
            "2019-12-30",
            "2019-12-31",
            "2020-01-02",
            "2020-01-03",
            "2021-01-04",
            "2021-01-05",
            "2023-01-03",
            "2023-01-04",
        ]
    )
    ts_off = pd.DataFrame(
        {
            "date": dates.strftime("%Y-%m-%d"),
            "N_used": [40] * len(dates),
            "p1": [0.22, 0.24, 0.71, 0.69, 0.33, 0.35, 0.16, 0.15],
            "deff": [18.0, 17.5, 4.0, 4.4, 10.0, 9.5, 24.0, 25.0],
            "turnover_pair_frac": [0.1, 0.12, 0.35, 0.31, 0.2, 0.21, 0.15, 0.16],
            "structure_score": [0.2] * len(dates),
            "insufficient_universe": [False] * len(dates),
        }
    )
    regime_df = pd.DataFrame(
        {
            "date": dates.strftime("%Y-%m-%d"),
            "regime": ["stable", "stable", "stress", "stress", "transition", "stable", "dispersion", "dispersion"],
            "exposure": [0.7, 0.7, 0.1, 0.1, 0.4, 0.7, 0.9, 0.9],
            "dp1_5": [0.0, 0.01, 0.6, 0.2, 0.35, 0.05, -0.4, -0.1],
            "ddeff_5": [0.0, -0.2, -5.0, -2.0, 2.6, 0.4, 3.2, 1.1],
        }
    )
    bt_df = pd.DataFrame(
        {
            "date": dates.strftime("%Y-%m-%d"),
            "strategy_simple_ret": [0.002, 0.003, -0.001, 0.001, 0.002, 0.002, 0.004, 0.003],
            "benchmark_simple_ret": [0.003, 0.004, -0.004, -0.001, 0.001, 0.002, 0.003, 0.002],
        }
    )

    era_df = _build_era_evaluation(ts_off=ts_off, regime_df=regime_df, bt_df=bt_df)
    assert not era_df.empty
    assert {"era", "alpha_ann_return", "dd_improvement", "share_stress", "share_dispersion"}.issubset(era_df.columns)
    assert {"2018_2019", "2020", "2021_2022", "2023_2026"}.issubset(set(era_df["era"].astype(str).tolist()))

    playbook = _build_action_playbook(regime_df=regime_df, ts_off=ts_off, bt_df=bt_df, horizon_days=2)
    assert not playbook.empty
    required = {
        "date",
        "regime",
        "action_code",
        "risk_stance",
        "signal_reliability",
        "signal_tier",
        "alpha_cum_future",
        "dd_improvement_future",
        "tradeoff_label",
    }
    assert required.issubset(set(playbook.columns))
    assert set(playbook["signal_tier"].astype(str).unique()).issubset({"high", "medium", "low"})


def test_ui_view_model_has_stable_contract_keys() -> None:
    dates = pd.date_range("2026-02-01", periods=3, freq="D")
    ts_off = pd.DataFrame(
        {
            "date": dates.strftime("%Y-%m-%d"),
            "N_used": [30, 30, 30],
            "p1": [0.20, 0.22, 0.21],
            "deff": [18.0, 17.8, 18.2],
            "insufficient_universe": [False, False, False],
        }
    )
    regime_df = pd.DataFrame(
        {
            "date": dates.strftime("%Y-%m-%d"),
            "regime": ["stable", "stable", "transition"],
            "exposure": [0.7, 0.7, 0.4],
            "dp1_5": [0.0, 0.02, 0.35],
            "ddeff_5": [0.0, -0.2, 1.5],
        }
    )
    playbook = pd.DataFrame(
        {
            "date": dates.strftime("%Y-%m-%d"),
            "regime": ["stable", "stable", "transition"],
            "action_code": ["BASELINE_RISK", "BASELINE_RISK", "DEFENSIVE_REBALANCE"],
            "risk_stance": ["balanced", "balanced", "cautious"],
            "signal_tier": ["medium", "medium", "low"],
            "signal_reliability": [0.55, 0.56, 0.42],
            "tradeoff_label": ["ok", "ok", "trade-off"],
        }
    )
    case_df = pd.DataFrame([{"case_regime": "stress", "date": "2020-03-16", "alpha_cum": -0.1}])
    era_df = pd.DataFrame([{"era": "2023_2026", "alpha_ann_return": 0.01}])
    op_payload = {"latest_date": "2026-02-03", "latest_events": ["TRANSITION_SPIKE"], "n_events_last_60d": 4}
    robust = {"joint_majority_60d": 0.33, "latest_joint_majority_5": 0.0}
    gate = {"blocked": False, "reasons": []}

    vm = _build_ui_view_model(
        run_id="20260213T999999Z",
        ts_off=ts_off,
        regime_df=regime_df,
        robust_metrics=robust,
        gate=gate,
        op_payload=op_payload,
        case_df=case_df,
        era_df=era_df,
        playbook_df=playbook,
    )

    assert vm["schema_version"] == "lab_corr_view_v1"
    assert vm["deployment_gate_blocked"] is False
    assert "latest_state" in vm and isinstance(vm["latest_state"], dict)
    assert "latest_regime" in vm and isinstance(vm["latest_regime"], dict)
    assert vm["alerts"]["latest_events"] == ["TRANSITION_SPIKE"]
    assert vm["playbook_latest"]["action_code"] == "DEFENSIVE_REBALANCE"
    assert isinstance(vm["case_preview"], list)
    assert isinstance(vm["era_summary"], list)
