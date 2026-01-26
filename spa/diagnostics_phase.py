import argparse
import json
import os
import re
from datetime import datetime
import hashlib

import numpy as np
import pandas as pd
import matplotlib
import csv

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401

from spa.models.takens_knn import TakensKNN, embed


def _infer_sep(path):
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        sample = f.read(4096)
    try:
        return csv.Sniffer().sniff(sample).delimiter
    except Exception:
        return ","


def _normalize_numeric(series):
    s = series.astype(str)
    s = s.str.replace(".", "", regex=False)
    s = s.str.replace(",", ".", regex=False)
    return pd.to_numeric(s, errors="coerce")


def _detect_time_col(df):
    candidates = [c for c in df.columns if re.search(r"(data|date|dia|hora|instante|timestamp|mes|mes|ano)", c, re.I)]
    best_col = None
    best_nonnull = -1
    for col in candidates:
        parsed = pd.to_datetime(df[col], errors="coerce")
        nonnull = parsed.notna().sum()
        if nonnull > best_nonnull:
            best_nonnull = nonnull
            best_col = col
    return best_col


def _detect_group_col(df):
    candidates = [
        c
        for c in df.columns
        if re.search(r"(subsistema|submercado|regiao|regiao|area|area|grupo)", c, re.I)
    ]
    if candidates:
        return candidates[0]
    return None


def _detect_value_col(df, time_col, group_col):
    best_col = None
    best_score = -1
    for col in df.columns:
        if col == time_col or col == group_col:
            continue
        nums = _normalize_numeric(df[col])
        score = nums.notna().mean()
        if score > best_score:
            best_score = score
            best_col = col
    return best_col


def _apply_filters(df, filters):
    for key, val in filters:
        if key in df.columns:
            df = df[df[key].astype(str) == val]
    return df


def _choose_split(dates, default_cutoff="2024-12-31"):
    dates = pd.Series(pd.to_datetime(dates, errors="coerce")).dropna()
    if dates.empty:
        return None, None
    max_year = dates.dt.year.max()
    cutoff = pd.Timestamp(default_cutoff)
    if max_year > cutoff.year:
        train_end = cutoff
        test_year = max_year
        return train_end, test_year
    # Use last full year as test
    train_year = max_year - 1
    if train_year >= dates.dt.year.min():
        train_end = pd.Timestamp(f"{train_year}-12-31")
        test_year = max_year
        return train_end, test_year
    return None, None


def _metrics(real, pred):
    real = np.asarray(real, dtype=float)
    pred = np.asarray(pred, dtype=float)
    err = pred - real
    mae = float(np.nanmean(np.abs(err))) if len(err) else np.nan
    rmse = float(np.sqrt(np.nanmean(err ** 2))) if len(err) else np.nan
    mape = np.nan
    nonzero = real != 0
    if np.any(nonzero):
        mape = float(np.nanmean(np.abs(err[nonzero] / real[nonzero])) * 100.0)
    return mae, rmse, mape


def _plot_series(dates, values, out_path, title):
    plt.figure(figsize=(10, 4))
    plt.plot(dates, values, color="#1f77b4", linewidth=1.2)
    plt.title(title)
    plt.xlabel("Data")
    plt.ylabel("Valor")
    plt.tight_layout()
    plt.savefig(out_path, dpi=160)
    plt.close()


def _plot_returns_hist(returns, out_path, title):
    plt.figure(figsize=(8, 4))
    plt.hist(returns, bins=60, color="#555555", alpha=0.85)
    plt.title(title)
    plt.xlabel("Retorno/diferenca")
    plt.ylabel("Frequencia")
    plt.tight_layout()
    plt.savefig(out_path, dpi=160)
    plt.close()


def _plot_attractor_2d(x, y, out_path, title):
    plt.figure(figsize=(6, 6))
    plt.scatter(x, y, s=4, alpha=0.6)
    plt.title(title)
    plt.xlabel("y(t)")
    plt.ylabel("y(t-)")
    plt.tight_layout()
    plt.savefig(out_path, dpi=160)
    plt.close()


def _plot_attractor_3d(x, y, z, out_path, title):
    fig = plt.figure(figsize=(7, 6))
    ax = fig.add_subplot(111, projection="3d")
    ax.scatter(x, y, z, s=3, alpha=0.6)
    ax.set_title(title)
    ax.set_xlabel("y(t)")
    ax.set_ylabel("y(t-tau)")
    ax.set_zlabel("y(t-2tau)")
    plt.tight_layout()
    plt.savefig(out_path, dpi=160)
    plt.close()


def _plot_pred_vs_real(dates, real, pred, out_path, title):
    plt.figure(figsize=(10, 4))
    plt.plot(dates, real, color="#1f77b4", label="Real", linewidth=1.2)
    plt.plot(dates, pred, color="#d62728", label="Previsto", linewidth=1.2)
    plt.title(title)
    plt.xlabel("Data")
    plt.ylabel("Valor")
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_path, dpi=160)
    plt.close()


def _plot_err_pct(dates, err_pct, out_path, title):
    plt.figure(figsize=(10, 4))
    plt.plot(dates, err_pct, color="#ff7f0e", linewidth=1.1)
    plt.axhline(0, color="#333333", linewidth=0.8)
    plt.title(title)
    plt.xlabel("Data")
    plt.ylabel("Erro %")
    plt.tight_layout()
    plt.savefig(out_path, dpi=160)
    plt.close()




def _plot_horizon_error(h, mape, threshold, h_useful, out_path, title):
    plt.figure(figsize=(7, 4))
    plt.plot(h, mape, marker="o", linewidth=1.2, label="MAPE")
    plt.axhline(threshold, color="#d62728", linestyle="--", linewidth=1.2, label="limiar")
    if h_useful:
        plt.axvline(h_useful, color="#2ca02c", linestyle="--", linewidth=1.2, label=f"horizonte = {h_useful}")
    plt.title(title)
    plt.xlabel("Horizonte (h)")
    plt.ylabel("MAPE (%)")
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_path, dpi=160)
    plt.close()

def _plot_divergence(h, dist, out_path, title):
    plt.figure(figsize=(7, 4))
    plt.plot(h, dist, marker="o", linewidth=1.2)
    plt.title(title)
    plt.xlabel("Passos")
    plt.ylabel("Distancia media")
    plt.tight_layout()
    plt.savefig(out_path, dpi=160)
    plt.close()

def _infer_returns(series):
    series = np.asarray(series, dtype=float)
    if np.any(series <= 0):
        return np.diff(series)
    return np.diff(np.log(series))


def _ami_curve(series, max_tau=60, bins=32):
    series = np.asarray(series, dtype=float)
    max_tau = min(max_tau, max(2, len(series) // 5))
    mi = []
    for tau in range(1, max_tau + 1):
        x = series[:-tau]
        y = series[tau:]
        hist, _, _ = np.histogram2d(x, y, bins=bins)
        pxy = hist / np.sum(hist)
        px = np.sum(pxy, axis=1)
        py = np.sum(pxy, axis=0)
        denom = px[:, None] * py[None, :]
        nz = (pxy > 0) & (denom > 0)
        mi_val = np.sum(pxy[nz] * np.log(pxy[nz] / denom[nz]))
        mi.append(mi_val)
    return np.array(mi)


def _first_local_min(values):
    if len(values) < 3:
        return int(np.argmin(values)) + 1
    for i in range(1, len(values) - 1):
        if values[i] < values[i - 1] and values[i] < values[i + 1]:
            return i + 1
    return int(np.argmin(values)) + 1


def _fnn_curve(series, tau, max_m=12, rtol=10.0, atol=2.0):
    series = np.asarray(series, dtype=float)
    max_m = min(max_m, 12)
    fnn = []
    for m in range(1, max_m + 1):
        start = (m - 1) * tau
        end = len(series) - tau
        if end - start <= 2:
            fnn.append(1.0)
            continue
        X = []
        Xp1 = []
        for i in range(start, end):
            X.append([series[i - j * tau] for j in range(m)])
            Xp1.append([series[i - j * tau] for j in range(m + 1)])
        X = np.array(X)
        Xp1 = np.array(Xp1)
        dists = np.linalg.norm(X[:, None, :] - X[None, :, :], axis=2)
        np.fill_diagonal(dists, np.inf)
        nn = np.argmin(dists, axis=1)
        dist_m = dists[np.arange(len(nn)), nn]
        dist_m[dist_m == 0] = 1e-9
        dist_mp1 = np.linalg.norm(Xp1 - Xp1[nn], axis=1)
        std_m = np.std(X, axis=0).mean()
        fnn_mask = (np.abs(dist_mp1 - dist_m) / dist_m > rtol) | (dist_mp1 / std_m > atol if std_m else True)
        fnn.append(float(np.mean(fnn_mask)))
    return np.array(fnn)


def _plot_curve(x, y, x_sel, out_path, title, xlabel):
    plt.figure(figsize=(7, 4))
    plt.plot(x, y, marker="o", linewidth=1.2)
    if x_sel is not None:
        plt.axvline(x_sel, color="#d62728", linestyle="--", linewidth=1.2)
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel("Value")
    plt.tight_layout()
    plt.savefig(out_path, dpi=160)
    plt.close()


def _ensure_sorted_dates(dates):
    if not dates.is_monotonic_increasing:
        raise ValueError("Datas fora de ordem; ordene antes de treinar/testar.")


def _split_hash(train_idx, test_idx):
    payload = np.concatenate([train_idx.astype(np.int64), test_idx.astype(np.int64)])
    return hashlib.sha256(payload.tobytes()).hexdigest()


def _validate_split(dates, train_end, test_year, train_end_idx, test_mask):
    _ensure_sorted_dates(dates)
    test_mask = np.asarray(test_mask, dtype=bool)
    train_mask = ~test_mask
    if not train_mask.any() or not test_mask.any():
        raise ValueError("Split inválido: treino ou teste vazio.")
    if train_end is not None:
        if dates[train_mask].max() > train_end:
            raise ValueError("Dados de treino passam do limite temporal.")
        if dates[test_mask].min() <= train_end:
            raise ValueError("Dados de teste incluem datas de treino.")
    if test_year is not None:
        years = pd.to_datetime(dates[test_mask]).dt.year.unique()
        if len(years) != 1 or years[0] != test_year:
            raise ValueError("Split temporal inconsistente com o ano de teste.")
    if np.any(np.arange(len(dates))[train_mask] > train_end_idx):
        raise ValueError("Indices de treino fora da janela esperada.")


def _safe_test_indices(test_mask, m, tau, train_end_pos):
    test_mask = np.asarray(test_mask, dtype=bool)
    test_indices = np.where(test_mask)[0]
    if test_indices.size == 0:
        return np.array([], dtype=int), 0
    test_start_idx = int(test_indices.min())
    min_valid = test_start_idx + (m - 1) * tau
    if min_valid <= train_end_pos:
        min_valid = train_end_pos + 1
    safe_indices = test_indices[test_indices >= min_valid]
    dropped = int(test_indices.size - safe_indices.size)
    return safe_indices, dropped


def _embedding_segment(series, start_idx, end_idx, tau, m):
    if end_idx - start_idx + 1 < (m - 1) * tau + 1:
        return np.array([])
    segment = series[start_idx : end_idx + 1]
    X = []
    for i in range((m - 1) * tau, len(segment)):
        X.append([segment[i - j * tau] for j in range(m)])
    return np.array(X)
def _safe_group_name(name):
    if name is None:
        return "TOTAL"
    text = str(name)
    if "Sudeste" in text or "Centro-Oeste" in text:
        return "SE-CO"
    if "Nordeste" in text:
        return "NE"
    if "Norte" in text:
        return "N"
    if "Sul" in text:
        return "S"
    safe = re.sub(r"[\\\\/]+", "-", text)
    safe = re.sub(r"\\s+", "_", safe).strip("_")
    return safe or "TOTAL"


def run_for_group(
    df,
    group_value,
    time_col,
    value_col,
    outdir,
    tau,
    m,
    k,
    auto_embed=False,
    max_tau=60,
    max_m=12,
    ami_bins=32,
    fnn_threshold=0.02,
    horizon=30,
    mape_threshold=5.0,
):
    df_g = df.copy()
    if group_value is not None:
        df_g = df_g[df_g["_group"] == group_value]
    df_g = df_g.dropna(subset=[time_col, value_col]).sort_values(time_col)
    df_g = df_g.reset_index(drop=True)
    if df_g.empty:
        return None

    dates = pd.to_datetime(df_g[time_col], errors="coerce")
    values = _normalize_numeric(df_g[value_col])
    mask = dates.notna() & values.notna()
    dates = dates[mask].reset_index(drop=True)
    values = values[mask].reset_index(drop=True)

    if len(values) < (m * tau + 10):
        return None

    os.makedirs(outdir, exist_ok=True)

    _plot_series(dates, values, os.path.join(outdir, "series_1d.png"), f"Serie 1D  {group_value or 'TOTAL'}")
    returns = _infer_returns(values)
    _plot_returns_hist(
        returns,
        os.path.join(outdir, "returns_hist.png"),
        f"Retornos/diferencas  {group_value or 'TOTAL'}",
    )

    tau_fixed = tau
    m_fixed = m
    if auto_embed:
        ami = _ami_curve(values, max_tau=max_tau, bins=ami_bins)
        tau = _first_local_min(ami)
        _plot_curve(
            np.arange(1, len(ami) + 1),
            ami,
            tau,
            os.path.join(outdir, "ami_curve.png"),
            f"AMI vs tau  {group_value or 'TOTAL'}",
            "tau",
        )
        fnn = _fnn_curve(values, tau=tau, max_m=max_m)
        m_candidates = np.arange(1, len(fnn) + 1)
        m_sel = None
        for i, v in enumerate(fnn):
            if v < fnn_threshold:
                m_sel = i + 1
                break
        if m_sel is None:
            m_sel = int(np.argmin(fnn)) + 1
        m = m_sel
        _plot_curve(
            m_candidates,
            fnn,
            m,
            os.path.join(outdir, "fnn_curve.png"),
            f"FNN vs m  {group_value or 'TOTAL'}",
            "m",
        )

    # Attractor plots
    idx_start = (m - 1) * tau
    x = values[idx_start:]
    y = values[idx_start - tau : -tau] if tau > 0 else values[idx_start:]
    z = values[idx_start - 2 * tau : -2 * tau] if 2 * tau > 0 else values[idx_start:]
    min_len = min(len(x), len(y), len(z))
    x = x[-min_len:]
    y = y[-min_len:]
    z = z[-min_len:]
    sample_n = min(4000, len(x))
    if sample_n > 0:
        idx = np.linspace(0, len(x) - 1, sample_n).astype(int)
        _plot_attractor_2d(
            x.iloc[idx] if hasattr(x, "iloc") else x[idx],
            y.iloc[idx] if hasattr(y, "iloc") else y[idx],
            os.path.join(outdir, "attractor_2d.png"),
            f"Atrator 2D (={tau}, m={m})  {group_value or 'TOTAL'}",
        )
        _plot_attractor_3d(
            x.iloc[idx] if hasattr(x, "iloc") else x[idx],
            y.iloc[idx] if hasattr(y, "iloc") else y[idx],
            z.iloc[idx] if hasattr(z, "iloc") else z[idx],
            os.path.join(outdir, "attractor_3d.png"),
            f"Atrator 3D (={tau}, m={m})  {group_value or 'TOTAL'}",
        )

    # Train/test split
    train_end, test_year = _choose_split(dates)
    if train_end is None:
        split_idx = int(len(values) * 0.8)
        train_end_idx = split_idx
        test_mask = np.arange(len(values)) > train_end_idx
        train_end_label = dates.iloc[train_end_idx].date().isoformat()
        test_year = dates.iloc[-1].year
    else:
        train_end_idx = dates[dates <= train_end].index.max()
        test_mask = dates > train_end
        train_end_label = train_end.date().isoformat()

    train_end_pos = int(train_end_idx) if train_end_idx == train_end_idx else int(len(values) * 0.8)
    _validate_split(dates, train_end, test_year, train_end_pos, test_mask)

    series = values.values
    model = TakensKNN(tau=tau, m=m, k=k)
    fit_ok = model.fit(series, train_end_pos)
    if not fit_ok:
        return None

    preds = []
    reals = []
    pred_dates = []
    err_abs = []
    err_pct = []
    baseline_preds = []

    test_indices, dropped = _safe_test_indices(test_mask, m, tau, train_end_pos)
    if test_indices.size == 0:
        return None
    for i in test_indices:
        state = np.array([series[i - j * tau] for j in range(m)], dtype=float)
        pred = model.predict_1step(state)
        if pred is None:
            continue
        real = series[i + 1]
        pred_date = dates.iloc[i + 1]
        preds.append(pred)
        reals.append(real)
        pred_dates.append(pred_date)
        err = pred - real
        err_abs.append(abs(err))
        if real != 0:
            err_pct.append(100.0 * err / real)
        else:
            err_pct.append(np.nan)
        baseline_preds.append(series[i])

    if not preds:
        return None

    preds = np.array(preds)
    reals = np.array(reals)
    baseline_preds = np.array(baseline_preds)
    mae, rmse, mape = _metrics(reals, preds)
    b_mae, b_rmse, b_mape = _metrics(reals, baseline_preds)
    better_baseline = mae < b_mae if not np.isnan(mae) and not np.isnan(b_mae) else False

    # Heuristic: correlation + shape stability
    corr = np.corrcoef(reals, preds)[0, 1] if len(reals) > 2 else 0.0
    train_embed = _embedding_segment(series, 0, train_end_pos, tau, m)
    test_embed = _embedding_segment(series, test_indices.min(), len(series) - 2, tau, m)
    if train_embed.size and test_embed.size:
        train_r = np.std(train_embed)
        test_r = np.std(test_embed)
        shape_ok = (test_r / train_r) < 1.5 if train_r else False
    else:
        shape_ok = False
    dynamics_captured = bool(corr > 0.3 and shape_ok)

    pred_df = pd.DataFrame(
        {
            "date": pred_dates,
            "real": reals,
            "pred": preds,
            "err_abs": err_abs,
            "err_pct": err_pct,
        }
    )
    pred_df.to_csv(os.path.join(outdir, "pred_vs_real.csv"), index=False)

    _plot_pred_vs_real(
        pred_dates,
        reals,
        preds,
        os.path.join(outdir, "pred_vs_real.png"),
        f"Previsto vs Real ({test_year})  {group_value or 'TOTAL'}",
    )
    _plot_err_pct(
        pred_dates,
        err_pct,
        os.path.join(outdir, "pred_error_pct.png"),
        f"Erro % - {group_value or 'TOTAL'}",
    )

    # Horizon evaluation (multi-step rollout)
    H = max(1, int(horizon))
    h_vals = np.arange(1, H + 1)
    mape_h = []
    rmse_h = []
    test_indices = [i for i in range((m - 1) * tau, len(series) - 1) if (test_mask[i] if isinstance(test_mask, np.ndarray) else bool(test_mask.iloc[i]))]
    for h in h_vals:
        errs = []
        errs_pct = []
        for i in test_indices:
            if i + h >= len(series):
                continue
            preds_h = model.predict_multistep(series, i, h)
            if preds_h is None or len(preds_h) < h:
                continue
            pred = preds_h[-1]
            real = series[i + h]
            err = pred - real
            errs.append(err)
            if real != 0:
                errs_pct.append(abs(err / real) * 100.0)
        if errs:
            errs = np.array(errs)
            mape_h.append(float(np.mean(errs_pct)) if errs_pct else np.nan)
            rmse_h.append(float(np.sqrt(np.mean(errs ** 2))))
        else:
            mape_h.append(np.nan)
            rmse_h.append(np.nan)

    h_useful = 0
    for h, mape_val in zip(h_vals, mape_h):
        if mape_val == mape_val and mape_val <= mape_threshold:
            h_useful = int(h)
        else:
            break

    _plot_horizon_error(
        h_vals,
        mape_h,
        mape_threshold,
        h_useful if h_useful > 0 else None,
        os.path.join(outdir, "horizon_error.png"),
        f"Erro vs horizonte - {group_value or 'TOTAL'}",
    )

    # Divergence indicator (simple neighbor separation)
    X, y_embed, idx_embed = embed(series, tau, m)
    div = []
    if X is not None and len(X) > 50:
        sample_n = min(200, len(X))
        sample_idx = np.linspace(0, len(X) - 1, sample_n).astype(int)
        Xs = X[sample_idx]
        dists = np.linalg.norm(Xs[:, None, :] - Xs[None, :, :], axis=2)
        np.fill_diagonal(dists, np.inf)
        nn = np.argmin(dists, axis=1)
        max_steps = min(10, H)
        for step in range(1, max_steps + 1):
            vals = []
            for a, b in zip(sample_idx, nn):
                if a + step < len(X) and b + step < len(X):
                    vals.append(np.linalg.norm(X[a + step] - X[b + step]))
            div.append(float(np.mean(vals)) if vals else np.nan)
        _plot_divergence(
            np.arange(1, len(div) + 1),
            div,
            os.path.join(outdir, "divergence.png"),
            f"Indicador de divergencia - {group_value or 'TOTAL'}",
        )

    summary = {
        "group": group_value or "TOTAL",
        "tau": tau,
        "m": m,
        "k": k,
        "auto_embed": bool(auto_embed),
        "tau_fixed": tau_fixed,
        "m_fixed": m_fixed,
        "train_end": train_end_label,
        "test_year": int(test_year) if test_year else None,
        "split_hash": _split_hash(np.where(~np.asarray(test_mask, dtype=bool))[0], test_indices),
        "dropped_test_points_due_to_embedding": int(dropped),
        "metrics": {"mae": mae, "rmse": rmse, "mape": mape},
        "baseline": {"mae": b_mae, "rmse": b_rmse, "mape": b_mape},
        "better_than_baseline": bool(better_baseline),
        "dynamics_captured": bool(dynamics_captured),
        "corr_pred_real": float(corr) if corr == corr else None,
        "shape_ok": bool(shape_ok),
        "horizon": {
            "H": H,
            "mape_threshold": mape_threshold,
            "mape_h": mape_h,
            "rmse_h": rmse_h,
            "horizon_useful": int(h_useful),
        },
        "horizon_note": (
            f"Horizonte util estimado: {h_useful} passo(s) com MAPE <= {mape_threshold:.1f}%."
            if h_useful > 0
            else f"MAPE ultrapassa {mape_threshold:.1f}% ja nos primeiros passos."
        ),
    }

    with open(os.path.join(outdir, "summary_phase.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    return summary


def main():
    parser = argparse.ArgumentParser(description="Diagnostico visual por subsistema (fase/embedding + baseline)")
    parser.add_argument("--input", required=True, help="CSV de entrada (normalizado ou processed.csv)")
    parser.add_argument("--time-col", default=None, help="Coluna de tempo")
    parser.add_argument("--value-col", default=None, help="Coluna de valor")
    parser.add_argument("--group-col", default=None, help="Coluna de grupo (subsistema)")
    parser.add_argument("--filter", action="append", default=[], help="Filtro KEY=VALUE (pode repetir)")
    parser.add_argument("--tau", type=int, default=4, help="Atraso tau")
    parser.add_argument("--m", type=int, default=4, help="Dimensao m")
    parser.add_argument("--k", type=int, default=10, help="k do kNN local")
    parser.add_argument("--auto-embed", action="store_true", help="Estimar tau/m via AMI + FNN")
    parser.add_argument("--max-tau", type=int, default=60, help="Tau maximo para AMI")
    parser.add_argument("--max-m", type=int, default=12, help="m maximo para FNN")
    parser.add_argument("--ami-bins", type=int, default=32, help="Bins para AMI")
    parser.add_argument("--fnn-threshold", type=float, default=0.02, help="Threshold FNN para escolher m")
    parser.add_argument("--horizon", type=int, default=30, help="Horizonte maximo (multi-step)")
    parser.add_argument("--mape-threshold", type=float, default=5.0, help="Limiar de MAPE para horizonte util")
    parser.add_argument("--outdir", default="results/phase", help="Diretorio de saida")
    args = parser.parse_args()

    sep = _infer_sep(args.input)
    df = pd.read_csv(args.input, sep=sep, dtype=str)

    time_col = args.time_col or _detect_time_col(df)
    group_col = args.group_col or _detect_group_col(df)
    value_col = args.value_col or _detect_value_col(df, time_col, group_col)

    if time_col is None or value_col is None:
        raise ValueError("Nao foi possivel detectar time_col/value_col. Use flags --time-col/--value-col.")

    filters = []
    for item in args.filter:
        if "=" in item:
            key, val = item.split("=", 1)
            filters.append((key, val))
    if filters:
        df = _apply_filters(df, filters)

    df["_group"] = df[group_col] if group_col else "TOTAL"

    outdir = args.outdir
    os.makedirs(outdir, exist_ok=True)

    summaries = []
    for group_value in sorted(df["_group"].dropna().unique()):
        group_dir = os.path.join(outdir, _safe_group_name(group_value))
        summary = run_for_group(
            df,
            group_value,
            time_col,
            value_col,
            group_dir,
            args.tau,
            args.m,
            args.k,
            auto_embed=args.auto_embed,
            max_tau=args.max_tau,
            max_m=args.max_m,
            ami_bins=args.ami_bins,
            fnn_threshold=args.fnn_threshold,
            horizon=args.horizon,
            mape_threshold=args.mape_threshold,
        )
        if summary:
            summaries.append(summary)

    with open(os.path.join(outdir, "summary_all.json"), "w", encoding="utf-8") as f:
        json.dump(summaries, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    main()
