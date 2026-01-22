import numpy as np
import pandas as pd


def embed(series, tau, m):
    series = np.asarray(series, dtype=float)
    start = (m - 1) * tau
    X = []
    idx = []
    for i in range(start, len(series)):
        X.append([series[i - j * tau] for j in range(m)])
        idx.append(i)
    if not X:
        return None, None
    return np.array(X), np.array(idx)


def _pca_anisotropy(X):
    if X.shape[0] < 2:
        return np.nan
    Xc = X - np.median(X, axis=0)
    cov = np.cov(Xc.T)
    vals = np.linalg.eigvalsh(cov)
    vals = np.sort(vals)[::-1]
    total = vals.sum()
    if total <= 0:
        return np.nan
    return float(vals[0] / total)


def _divergence_rate(X, delta=1, max_pairs=300):
    n = X.shape[0]
    if n < delta + 2:
        return np.nan
    idxs = np.arange(n - delta)
    if len(idxs) > max_pairs:
        idxs = np.linspace(0, len(idxs) - 1, max_pairs).astype(int)
    ratios = []
    for i in idxs:
        xi = X[i]
        dists = np.linalg.norm(X[: n - delta] - xi, axis=1)
        dists[i] = np.inf
        j = int(np.argmin(dists))
        d0 = dists[j]
        if not np.isfinite(d0) or d0 <= 0:
            continue
        d1 = np.linalg.norm(X[i + delta] - X[j + delta])
        if not np.isfinite(d1) or d1 <= 0:
            continue
        ratios.append(np.log(d1 / d0))
    if not ratios:
        return np.nan
    return float(np.mean(ratios))


def compute_phase_features(series, dates, tau=2, m=4, window=252, delta=1):
    X, idx = embed(series, tau, m)
    if X is None:
        return None
    dates = np.asarray(dates)
    rows = []
    prev_mu = None
    for i in range(window, X.shape[0] + 1):
        Xw = X[i - window : i]
        mu = np.median(Xw, axis=0)
        diff = Xw - mu
        raio_rms = float(np.sqrt(np.mean(np.sum(diff ** 2, axis=1))))
        anisotropy = _pca_anisotropy(Xw)
        drift_local = float(np.linalg.norm(mu - prev_mu)) if prev_mu is not None else 0.0
        divergence = _divergence_rate(Xw, delta=delta)
        r_window = series[idx[i - window : i]]
        autocorr = float(pd.Series(r_window).autocorr(lag=1)) if len(r_window) > 2 else np.nan
        rows.append(
            {
                "date": dates[idx[i - 1]],
                "raio_rms": raio_rms,
                "anisotropia": anisotropy,
                "drift_local": drift_local,
                "divergence_rate": divergence,
                "autocorr": autocorr,
            }
        )
        prev_mu = mu
    return pd.DataFrame(rows)
