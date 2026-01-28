from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, Tuple

import numpy as np
import pandas as pd


@dataclass
class FinancialDatasetSpec:
    entity_name: str
    freq: str
    date_col: str = "date"
    price_col: str | None = None
    return_col: str | None = None
    vol_col: str | None = None
    target_type: str = "log_return"  # log_return | simple_return | volatility
    winsorize: bool = True
    clip_low: float = 0.005
    clip_high: float = 0.995
    standardize: bool = False
    vol_window: int = 20


@dataclass
class ExperimentSpec:
    universe: Iterable[str]
    freq: str = "daily"
    target_type: str = "log_return"
    horizons: Iterable[int] = field(default_factory=lambda: (1, 5, 20))
    start_year: int = 2000
    end_year: int = 2025
    retrain_frequency: str = "yearly"
    models_to_compare: Iterable[str] = field(default_factory=lambda: ("naive", "motor"))


def prepare_financial_series(df: pd.DataFrame, spec: FinancialDatasetSpec) -> Tuple[pd.DataFrame, Dict[str, object]]:
    out = df.copy()
    if spec.date_col not in out.columns:
        raise ValueError("date_col nao encontrado")
    out[spec.date_col] = pd.to_datetime(out[spec.date_col], errors="coerce")
    out = out.dropna(subset=[spec.date_col]).sort_values(spec.date_col)
    out = out.drop_duplicates(subset=[spec.date_col], keep="last")

    if spec.target_type in {"log_return", "simple_return"}:
        if spec.return_col and spec.return_col in out.columns:
            y_raw = out[spec.return_col].astype(float)
        elif spec.price_col and spec.price_col in out.columns:
            price = out[spec.price_col].astype(float)
            if spec.target_type == "log_return":
                y_raw = np.log(price).diff()
            else:
                y_raw = price.pct_change()
        else:
            raise ValueError("price_col ou return_col obrigatorio")
    elif spec.target_type == "volatility":
        if spec.vol_col and spec.vol_col in out.columns:
            y_raw = out[spec.vol_col].astype(float)
        elif spec.price_col and spec.price_col in out.columns:
            price = out[spec.price_col].astype(float)
            log_r = np.log(price).diff()
            window = max(2, int(spec.vol_window))
            y_raw = log_r.rolling(window, min_periods=window).std()
        else:
            raise ValueError("vol_col ou price_col obrigatorio para volatility")
    else:
        raise ValueError("target_type invalido")

    out = out.assign(y_raw=y_raw)
    out = out.dropna(subset=["y_raw"])

    metadata: Dict[str, object] = {
        "entity_name": spec.entity_name,
        "freq": spec.freq,
        "target_type": spec.target_type,
    }

    # sanity: scale check for returns
    if spec.target_type in {"log_return", "simple_return"}:
        if out["y_raw"].abs().max() > 2:
            metadata["warning_scale"] = "RETORNO_FORA_ESCALA"

    # winsorize/clipping
    if spec.winsorize:
        lo = float(out["y_raw"].quantile(spec.clip_low))
        hi = float(out["y_raw"].quantile(spec.clip_high))
        out["y_raw"] = out["y_raw"].clip(lo, hi)
        metadata["clip_low"] = lo
        metadata["clip_high"] = hi

    out = out.rename(columns={spec.date_col: "date"})
    out = out.assign(y=out["y_raw"])

    return out[["date", "y", "y_raw"]].copy(), metadata


def split_train_test(df: pd.DataFrame, train_end: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
    cutoff = pd.Timestamp(train_end)
    train = df[df["date"] <= cutoff].copy()
    test = df[df["date"] > cutoff].copy()
    return train, test


def standardize_train_test(train: pd.DataFrame, test: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, float]]:
    mu = float(train["y"].mean())
    sd = float(train["y"].std()) if float(train["y"].std()) != 0 else 1.0
    train = train.copy()
    test = test.copy()
    train["y"] = (train["y"] - mu) / sd
    test["y"] = (test["y"] - mu) / sd
    return train, test, {"mean": mu, "std": sd}


def mae(y_true, y_pred) -> float:
    return float(np.mean(np.abs(y_true - y_pred)))


def rmse(y_true, y_pred) -> float:
    return float(np.sqrt(np.mean((y_true - y_pred) ** 2)))


def smape(y_true, y_pred, eps: float = 1e-6) -> float:
    denom = np.abs(y_true) + np.abs(y_pred) + eps
    return float(np.mean(2 * np.abs(y_pred - y_true) / denom))


def mase(y_true, y_pred, naive_pred) -> float:
    denom = np.mean(np.abs(y_true - naive_pred))
    if denom == 0:
        return float("nan")
    return float(np.mean(np.abs(y_true - y_pred)) / denom)


def directional_accuracy(y_true, y_pred) -> float:
    return float(np.mean(np.sign(y_true) == np.sign(y_pred)))


def compute_metrics(y_true_raw, y_pred_raw, y_true_std, y_pred_std, naive_pred_raw, target_type: str) -> Dict[str, float]:
    metrics = {
        "mae_raw": mae(y_true_raw, y_pred_raw),
        "rmse_raw": rmse(y_true_raw, y_pred_raw),
        "mae_std": mae(y_true_std, y_pred_std),
        "rmse_std": rmse(y_true_std, y_pred_std),
        "mase": mase(y_true_raw, y_pred_raw, naive_pred_raw),
    }
    if target_type in {"log_return", "simple_return"}:
        metrics["dir_acc"] = directional_accuracy(y_true_raw, y_pred_raw)
    return metrics


def compute_confidence_finance(metrics: Dict[str, float], error_std: float, transition_rate: float, novelty: float) -> Dict[str, object]:
    breakdown = []
    def add(name, raw, norm, weight, comment):
        breakdown.append({
            "metric_name": name,
            "raw_value": raw,
            "normalized_value": norm,
            "weight": weight,
            "contribution": norm * weight,
            "comment": comment,
        })

    # normalize metrics
    mase = metrics.get("mase", float("nan"))
    dir_acc = metrics.get("dir_acc", float("nan"))
    mase_norm = 1.0 if mase != mase else float(np.clip(1.5 - mase, 0.0, 1.0))
    dir_norm = 0.0 if dir_acc != dir_acc else float(np.clip((dir_acc - 0.5) / 0.2, 0.0, 1.0))
    err_norm = float(np.clip(1.0 - error_std, 0.0, 1.0))
    trans_norm = float(np.clip(1.0 - transition_rate, 0.0, 1.0))
    nov_norm = float(np.clip(1.0 - novelty, 0.0, 1.0))

    add("mase", mase, mase_norm, 0.35, "<1 melhor que naive")
    add("dir_acc", dir_acc, dir_norm, 0.2, ">0.52 melhor")
    add("error_stability", error_std, err_norm, 0.2, "variancia do erro")
    add("transition_rate", transition_rate, trans_norm, 0.15, "instabilidade de mercado")
    add("novelty", novelty, nov_norm, 0.1, "fora de distribuicao")

    score = float(np.clip(sum(item["contribution"] for item in breakdown) * 100.0, 0.0, 100.0))
    if score >= 70:
        level = "HIGH"
        action = "OPERAR"
        verdict = "SIM"
    elif score >= 50:
        level = "MED"
        action = "REDUZIR_RISCO"
        verdict = "DEPENDE"
    else:
        level = "LOW"
        action = "NAO_OPERAR"
        verdict = "NAO"

    reasons = []
    if mase != mase or mase >= 1:
        reasons.append("MASE ruim")
    if dir_acc == dir_acc and dir_acc < 0.52:
        reasons.append("direcao fraca")
    if transition_rate > 0.3:
        reasons.append("mercado instavel")
    if novelty > 0.7:
        reasons.append("fora de distribuicao")

    return {
        "score": round(score, 2),
        "level": level,
        "action": action,
        "verdict": verdict,
        "reasons": reasons[:6],
        "breakdown": breakdown,
    }


def plot_master_finance(dates, y_raw, y_pred, naive_pred, out_path, verdict: Dict[str, object]):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(2, 1, figsize=(10, 6), sharex=True)
    axes[0].plot(dates, y_raw, label="y_raw", color="#0f172a", linewidth=1.0)
    axes[0].plot(dates, y_pred, label="y_pred", color="#1d4ed8", linewidth=0.9)
    axes[0].plot(dates, naive_pred, label="naive", color="#d97706", linewidth=0.9)
    axes[0].legend()
    axes[0].set_title("Target vs Pred (test)")

    err = y_raw - y_pred
    axes[1].plot(dates, err, color="#ef4444", linewidth=0.9)
    axes[1].axhline(0, color="#333333", linewidth=0.6)
    axes[1].set_title("Residual (y_raw - y_pred)")

    text = (
        f"verdict: {verdict.get('verdict')}\n"
        f"level: {verdict.get('level')}\n"
        f"score: {verdict.get('score')}\n"
        f"action: {verdict.get('action')}\n"
        f"reasons: {', '.join(verdict.get('reasons', []))}"
    )
    fig.text(0.02, 0.02, text, fontsize=9)

    fig.tight_layout()
    fig.savefig(out_path, dpi=160)
    plt.close(fig)
