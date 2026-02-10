
import argparse
from pathlib import Path
import json
import sys
import os
from datetime import datetime

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score, f1_score, balanced_accuracy_score, confusion_matrix

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from engine.diagnostics.regime_labels import RegimeClassifier
from engine.diagnostics.macro_context import load_macro_events


def _load_local_csv(ticker: str) -> pd.DataFrame | None:
    base = Path('data/raw/finance/yfinance_daily')
    path = base / f"{ticker}.csv"
    if not path.exists():
        alt = base / f"{ticker.replace('^','')}.csv"
        if alt.exists():
            path = alt
        else:
            return None
    df = pd.read_csv(path)
    if 'date' not in df.columns or 'r' not in df.columns:
        return None
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    df = df.dropna(subset=['date', 'r']).sort_values('date')
    return df


def _realized_vol(series: pd.Series, window: int) -> pd.Series:
    return series.rolling(window).std()


def _rolling_skew(series: pd.Series, window: int) -> pd.Series:
    return series.rolling(window).skew()


def _rolling_kurt(series: pd.Series, window: int) -> pd.Series:
    return series.rolling(window).kurt()


def _rolling_acf(series: pd.Series, window: int, lag: int) -> pd.Series:
    def _acf(x):
        if x.size <= lag:
            return np.nan
        s0 = x[:-lag]
        s1 = x[lag:]
        if np.std(s0) == 0 or np.std(s1) == 0:
            return 0.0
        return float(np.corrcoef(s0, s1)[0, 1])
    return series.rolling(window).apply(_acf, raw=True)


def _build_features(df: pd.DataFrame, use_embedding: bool = True) -> pd.DataFrame:
    r = df['r'].astype(float)
    feats = pd.DataFrame(index=df.index)
    for lag in range(1, 6):
        feats[f'r_lag{lag}'] = r.shift(lag)
    # rolling features shifted by 1 to avoid leakage
    feats['vol_5'] = _realized_vol(r, 5).shift(1)
    feats['vol_20'] = _realized_vol(r, 20).shift(1)
    feats['skew_20'] = _rolling_skew(r, 20).shift(1)
    feats['kurt_20'] = _rolling_kurt(r, 20).shift(1)
    for lag in range(1, 4):
        feats[f'acf{lag}_20'] = _rolling_acf(r, 20, lag).shift(1)
    if use_embedding:
        tau = 1
        m = 3
        values = r.to_numpy()
        min_len = (m - 1) * tau + 1
        if len(values) >= min_len:
            embed_len = len(values) - (m - 1) * tau
            cols = [
                values[(m - 1 - lag) * tau : (m - 1 - lag) * tau + embed_len]
                for lag in range(m)
            ]
            emb = np.column_stack(cols)
            emb_df = pd.DataFrame(emb, columns=[f'emb_{i}' for i in range(m)])
            emb_df.index = df.index[(m - 1) * tau : (m - 1) * tau + embed_len]
            feats = feats.join(emb_df.shift(1), how='left')
    return feats


def _standardize_train_test(X_train: pd.DataFrame, X_test: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    mean = X_train.mean(axis=0)
    std = X_train.std(axis=0).replace(0, 1.0)
    return (X_train - mean) / std, (X_test - mean) / std


def _make_target(df: pd.DataFrame, train_end: pd.Timestamp) -> tuple[pd.Series, float]:
    vol20 = _realized_vol(df['r'].astype(float), 20)
    train_mask = df['date'] <= train_end
    q70 = float(vol20[train_mask].quantile(0.7))
    target = (vol20 > q70).astype(int)
    return target, q70


def _baseline_rule(vol5: pd.Series, vol20: pd.Series) -> pd.Series:
    return (vol5 > vol20).astype(int)


def _fit_models(X_train, y_train):
    lr = LogisticRegression(max_iter=200)
    rf = RandomForestClassifier(n_estimators=200, random_state=42, class_weight='balanced')
    lr.fit(X_train, y_train)
    rf.fit(X_train, y_train)
    return lr, rf


def _evaluate(y_true, y_pred, y_prob):
    metrics = {
        'roc_auc': float(roc_auc_score(y_true, y_prob)) if len(np.unique(y_true)) > 1 else float('nan'),
        'f1': float(f1_score(y_true, y_pred)),
        'balanced_acc': float(balanced_accuracy_score(y_true, y_pred)),
        'confusion': confusion_matrix(y_true, y_pred).tolist(),
    }
    return metrics


def _regime_classifier_predict(df, target, train_mask):
    series = df['r'].astype(float).to_numpy()
    clf = RegimeClassifier(clustering_method='auto')
    try:
        embedded = clf.embed(series)
        velocity = clf.compute_velocity(series)
        energy = clf.compute_energy(embedded[:, 0], velocity)
        local_features = clf.compute_local_features(embedded[:, 0])
        cluster_features = {'velocity': velocity, 'energy': energy}
        cluster_features.update(local_features)
        labels = clf.cluster_states(embedded, cluster_features)
    except Exception:
        labels = np.zeros(len(series) - 2, dtype=int) if len(series) > 2 else np.zeros(len(series), dtype=int)
    start = (clf.m - 1) * clf.tau
    label_idx = df.index[start : start + len(labels)]
    label_series = pd.Series(labels, index=label_idx)
    target_aligned = target.loc[label_idx]
    train_mask_aligned = train_mask.loc[label_idx]
    probs = {}
    for lab in np.unique(labels):
        mask = (label_series == lab) & train_mask_aligned
        if mask.any():
            probs[int(lab)] = float(target_aligned[mask].mean())
        else:
            probs[int(lab)] = float(target_aligned[train_mask_aligned].mean())
    pred_prob = label_series.map(lambda x: probs.get(int(x), 0.0)).astype(float)
    pred_label = (pred_prob >= 0.5).astype(int)
    return pred_label, pred_prob


def _plot_vol_prob(dates, vol20, prob, out_path, title, events):
    fig, ax1 = plt.subplots(figsize=(10, 4))
    ax1.plot(dates, vol20, color='#0f172a', label='vol_20', linewidth=1.1)
    ax2 = ax1.twinx()
    ax2.plot(dates, prob, color='#1d4ed8', label='prob(vol_alta)', linewidth=1.0)
    ax1.set_xlabel('Data')
    ax1.set_ylabel('Vol 20d')
    ax2.set_ylabel('Prob')
    ax1.set_title(title)
    if events:
        for ev in events:
            ax1.axvspan(ev['start'], ev['end'], color='#f59e0b', alpha=0.15)
    fig.tight_layout()
    fig.savefig(out_path, dpi=160)
    plt.close(fig)


def _plot_master(dates, vol20, prob, target, out_path, verdict, warnings):
    fig, ax1 = plt.subplots(figsize=(10, 5))
    ax1.plot(dates, vol20, color="#0f172a", label="vol_20", linewidth=1.1)
    ax2 = ax1.twinx()
    ax2.plot(dates, prob, color="#1d4ed8", label="prob(vol_alta)", linewidth=1.0)
    ax1.set_title("Regime de Volatilidade + Prob")
    ax1.set_xlabel("Data")
    ax1.set_ylabel("Vol 20d")
    ax2.set_ylabel("Prob")

    text = (
        f"verdict: {verdict.get('verdict')}\n"
        f"level: {verdict.get('level')}\n"
        f"score: {verdict.get('score')}\n"
        f"action: {verdict.get('action')}\n"
        f"warnings: {', '.join(warnings) if warnings else 'none'}"
    )
    fig.text(0.02, 0.02, text, fontsize=9)
    fig.tight_layout()
    fig.savefig(out_path, dpi=160)
    plt.close(fig)


def _aggregate_events(md_path: Path, asset: str):
    events = load_macro_events(md_path)
    out = []
    for ev in events:
        if asset.lower() not in ev.asset.lower():
            continue
        out.append({
            'start': pd.Timestamp(ev.date_start),
            'end': pd.Timestamp(ev.date_end),
            'desc': ev.description,
        })
    return out


def _transition_score(df, train_mask, k=5, tau=1, m=3):
    series = df['r'].astype(float).to_numpy()
    min_len = (m - 1) * tau + 1
    if len(series) < min_len + 5:
        return pd.Series(index=df.index, dtype=float)
    embed_len = len(series) - (m - 1) * tau
    cols = [
        series[(m - 1 - lag) * tau : (m - 1 - lag) * tau + embed_len]
        for lag in range(m)
    ]
    emb = np.column_stack(cols)
    idx = df.index[(m - 1) * tau : (m - 1) * tau + embed_len]
    emb_df = pd.DataFrame(emb, columns=[f'emb_{i}' for i in range(m)], index=idx)
    train_emb = emb_df[train_mask.loc[idx]].to_numpy()
    scores = []
    for row in emb_df.to_numpy():
        if train_emb.shape[0] == 0:
            scores.append(np.nan)
            continue
        dists = np.linalg.norm(train_emb - row, axis=1)
        k_eff = min(k, len(dists))
        topk = np.partition(dists, k_eff - 1)[:k_eff]
        scores.append(float(np.mean(topk)))
    return pd.Series(scores, index=idx)


def _precision_at_k(score_weekly: pd.Series, event_weeks: set, k: int) -> float:
    top = score_weekly.sort_values(ascending=False).head(k).index
    hits = sum(1 for w in top if w in event_weeks)
    return hits / max(k, 1)


def _lead_lag(score_weekly: pd.Series, event_weeks: set):
    if score_weekly.empty or not event_weeks:
        return []
    top_weeks = score_weekly.sort_values(ascending=False).head(len(event_weeks)).index
    diffs = []
    for ev in event_weeks:
        closest = min(top_weeks, key=lambda w: abs((w - ev).days))
        diffs.append((closest - ev).days)
    return diffs


def _compute_confidence_risk(metrics: dict, transition_rate: float, novelty: float) -> dict:
    breakdown = []

    def add(name, raw, norm, weight, comment):
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

    roc = metrics.get("roc_auc", float("nan"))
    bal = metrics.get("balanced_acc", float("nan"))
    f1 = metrics.get("f1", float("nan"))
    roc_norm = 0.0 if roc != roc else float(np.clip((roc - 0.5) / 0.3, 0.0, 1.0))
    bal_norm = 0.0 if bal != bal else float(np.clip((bal - 0.5) / 0.3, 0.0, 1.0))
    f1_norm = 0.0 if f1 != f1 else float(np.clip(f1 / 0.8, 0.0, 1.0))
    trans_norm = float(np.clip(1.0 - transition_rate, 0.0, 1.0))
    nov_norm = float(np.clip(1.0 - novelty, 0.0, 1.0))

    add("roc_auc", roc, roc_norm, 0.35, "capacidade discriminativa")
    add("balanced_acc", bal, bal_norm, 0.25, "equilibrio de classes")
    add("f1", f1, f1_norm, 0.15, "qualidade geral")
    add("transition_rate", transition_rate, trans_norm, 0.15, "instabilidade de regime")
    add("novelty", novelty, nov_norm, 0.10, "fora de distribuicao")

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
    if roc != roc or roc < 0.55:
        reasons.append("roc_auc fraco")
    if bal != bal or bal < 0.52:
        reasons.append("bal_acc fraco")
    if transition_rate > 0.3:
        reasons.append("regime instavel")
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


def run_asset(ticker: str, outdir: Path, train_end: str, events_md: Path):
    df = _load_local_csv(ticker)
    if df is None or df.empty:
        return None
    df = df.copy()
    df['date'] = pd.to_datetime(df['date'])

    features = _build_features(df)
    target, q70 = _make_target(df, pd.Timestamp(train_end))
    vol20 = _realized_vol(df['r'].astype(float), 20)
    vol5 = _realized_vol(df['r'].astype(float), 5)

    data = features.join(target.rename('target')).join(vol20.rename('vol20')).join(vol5.rename('vol5'))
    data = data.dropna()
    train_mask = data.index.map(lambda i: df.loc[i, 'date'] <= pd.Timestamp(train_end))
    train_mask = pd.Series(train_mask, index=data.index)

    X = data.drop(columns=['target', 'vol20', 'vol5'])
    y = data['target'].astype(int)

    X_train = X[train_mask]
    X_test = X[~train_mask]
    y_train = y[train_mask]
    y_test = y[~train_mask]

    if X_test.empty or X_train.empty:
        return None

    X_train_s, X_test_s = _standardize_train_test(X_train, X_test)

    base_pred = _baseline_rule(data['vol5'], data['vol20']).loc[X_test.index]
    base_prob = base_pred.astype(float)

    lr, rf = _fit_models(X_train_s, y_train)
    lr_prob = lr.predict_proba(X_test_s)[:, 1]
    rf_prob = rf.predict_proba(X_test_s)[:, 1]
    lr_pred = (lr_prob >= 0.5).astype(int)
    rf_pred = (rf_prob >= 0.5).astype(int)

    motor_pred, motor_prob = _regime_classifier_predict(df, target, df['date'] <= pd.Timestamp(train_end))
    motor_pred = motor_pred.reindex(X_test.index).fillna(0).astype(int)
    motor_prob = motor_prob.reindex(X_test.index).fillna(0.0).astype(float)

    metrics = {
        'baseline': _evaluate(y_test, base_pred, base_prob),
        'logreg': _evaluate(y_test, lr_pred, lr_prob),
        'rf': _evaluate(y_test, rf_pred, rf_prob),
        'motor': _evaluate(y_test, motor_pred, motor_prob),
    }

    # confidence/verdict based on motor
    motor_metrics = metrics["motor"]
    transition_rate = float(np.mean(motor_pred.diff().fillna(0) != 0)) if len(motor_pred) > 1 else 0.0
    score_series = _transition_score(df, df['date'] <= pd.Timestamp(train_end))
    novelty = 0.0
    if not score_series.empty:
        max_train_idx = data.index[train_mask].max() if train_mask.any() else data.index.max()
        train_scores = score_series.loc[score_series.index <= max_train_idx].dropna()
        if not train_scores.empty:
            last_score = float(score_series.dropna().iloc[-1])
            mu = float(train_scores.mean())
            sd = float(train_scores.std()) if float(train_scores.std()) != 0 else 1.0
            novelty = float(np.clip(abs((last_score - mu) / sd) / 3.0, 0.0, 1.0))

    verdict = _compute_confidence_risk(motor_metrics, transition_rate, novelty)
    warnings = []
    if transition_rate > 0.3:
        warnings.append("REGIME_INSTAVEL")
    if novelty > 0.7:
        warnings.append("FORA_DISTRIBUICAO")
    if len(np.unique(motor_pred.dropna())) <= 1:
        warnings.append("COLAPSO_CLUSTER")

    outdir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame({
        'date': df.loc[X_test.index, 'date'],
        'target': y_test,
        'baseline_prob': base_prob,
        'logreg_prob': lr_prob,
        'rf_prob': rf_prob,
        'motor_prob': motor_prob,
    }).to_csv(outdir / 'pred_vs_true.csv', index=False)

    events = _aggregate_events(events_md, ticker)
    _plot_vol_prob(
        df.loc[X_test.index, 'date'],
        vol20.loc[X_test.index],
        lr_prob,
        outdir / 'vol_prob_logreg.png',
        f"{ticker} vol_20 vs prob(vol_alta)",
        events,
    )

    score = _transition_score(df, df['date'] <= pd.Timestamp(train_end))
    score_weekly = score.dropna()
    score_weekly.index = pd.to_datetime(score_weekly.index)
    score_weekly = score_weekly.resample('W-FRI').mean()
    event_weeks = set()
    if not score_weekly.empty:
        min_w = score_weekly.index.min()
        max_w = score_weekly.index.max()
    for ev in events:
        week = pd.Timestamp(ev['start']).to_period('W-FRI').start_time
        if not score_weekly.empty and (week < min_w or week > max_w):
            continue
        event_weeks.add(week)
    prec_k5 = _precision_at_k(score_weekly, event_weeks, 5)
    prec_k10 = _precision_at_k(score_weekly, event_weeks, 10)
    lead_lag = _lead_lag(score_weekly, event_weeks)

    report = {
        'ticker': ticker,
        'train_end': train_end,
        'q70': q70,
        'metrics': metrics,
        'transition': {
            'precision_at_5': prec_k5,
            'precision_at_10': prec_k10,
            'lead_lag_days': lead_lag,
        },
    }
    with (outdir / 'metrics.json').open('w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)

    # meta + summary + confidence + verdict + master plot
    meta = {
        "run_id": datetime.utcnow().strftime("%Y%m%d_%H%M%S"),
        "ticker": ticker,
        "freq": "daily",
        "method": "risk_regime",
        "train_end": train_end,
        "n_samples": int(len(df)),
        "warnings": warnings,
    }
    (outdir / "meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")

    summary_cols = [
        "run_id",
        "entity_name",
        "system_type",
        "ticker",
        "freq",
        "method",
        "n_samples",
        "dt",
        "m",
        "tau",
        "cluster_id",
        "label",
        "pct_time",
        "n_segments",
        "mean_duration",
        "std_duration",
        "energy_mean",
        "energy_std",
        "entropy_mean",
        "recurrence_mean",
        "notes",
    ]
    summary_row = {
        "run_id": meta["run_id"],
        "entity_name": ticker,
        "system_type": "finance",
        "ticker": ticker,
        "freq": "daily",
        "method": "risk_regime",
        "n_samples": int(len(df)),
        "dt": 1,
        "m": 3,
        "tau": 1,
        "cluster_id": np.nan,
        "label": "vol_alta",
        "pct_time": float(y.mean()),
        "n_segments": np.nan,
        "mean_duration": np.nan,
        "std_duration": np.nan,
        "energy_mean": np.nan,
        "energy_std": np.nan,
        "entropy_mean": np.nan,
        "recurrence_mean": np.nan,
        "notes": f"q70={q70:.6f}",
    }
    pd.DataFrame([summary_row], columns=summary_cols).to_csv(outdir / "summary.csv", index=False)

    breakdown_df = pd.DataFrame(verdict["breakdown"])
    breakdown_df.to_csv(outdir / "confidence_breakdown.csv", index=False)
    (outdir / "verdict.json").write_text(json.dumps(verdict, indent=2, ensure_ascii=False), encoding="utf-8")

    _plot_master(
        df.loc[X_test.index, "date"],
        vol20.loc[X_test.index],
        motor_prob,
        y_test,
        outdir / "master_plot.png",
        verdict,
        warnings,
    )
    return report


def main():
    parser = argparse.ArgumentParser(description='Finance risk regime benchmark (volatility)')
    parser.add_argument('--tickers', default='SPY,^VIX,GLD,DGS10,DX-Y')
    parser.add_argument('--train-end', default='2024-12-31')
    parser.add_argument('--outdir', default='results/finance_risk')
    parser.add_argument('--events-md', default='results/vix_context.md')
    args = parser.parse_args()

    tickers = [t.strip() for t in args.tickers.split(',') if t.strip()]
    out_root = Path(args.outdir)
    out_root.mkdir(parents=True, exist_ok=True)
    events_md = Path(args.events_md)

    summaries = []
    for ticker in tickers:
        outdir = out_root / ticker.replace('^', '')
        report = run_asset(ticker, outdir, args.train_end, events_md)
        if report:
            summaries.append(report)

    lines = [
        '# Finance Risk Regime Report',
        '',
        '| ticker | model | roc_auc | f1 | bal_acc |',
        '| --- | --- | --- | --- | --- |',
    ]
    for rep in summaries:
        for model, metrics in rep['metrics'].items():
            lines.append(
                f"| {rep['ticker']} | {model} | {metrics['roc_auc']:.4f} | {metrics['f1']:.4f} | {metrics['balanced_acc']:.4f} |"
            )
    lines.append('')
    lines.append('## Transition detection')
    lines.append('')
    lines.append('| ticker | precision@5 | precision@10 | lead/lag (dias) |')
    lines.append('| --- | --- | --- | --- |')
    for rep in summaries:
        trans = rep['transition']
        lines.append(
            f"| {rep['ticker']} | {trans['precision_at_5']:.2f} | {trans['precision_at_10']:.2f} | {trans['lead_lag_days']} |"
        )

    (out_root / 'report.md').write_text('\n'.join(lines), encoding='utf-8')


if __name__ == '__main__':
    main()

