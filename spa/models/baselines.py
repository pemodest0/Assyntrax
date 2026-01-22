import numpy as np


def persistence_next(series):
    series = np.asarray(series, dtype=float)
    return series[:-1]


def zero_mean_next(series):
    series = np.asarray(series, dtype=float)
    return np.zeros(len(series) - 1)


def ar1_fit(series):
    series = np.asarray(series, dtype=float)
    x = series[:-1]
    y = series[1:]
    denom = np.dot(x, x)
    if denom == 0:
        return 0.0
    return float(np.dot(x, y) / denom)


def ar1_predict(series, a):
    series = np.asarray(series, dtype=float)
    return a * series[:-1]


def moving_average(series, window):
    series = np.asarray(series, dtype=float)
    if len(series) < window:
        return np.array([])
    cumsum = np.cumsum(series)
    ma = (cumsum[window - 1 :] - np.concatenate(([0.0], cumsum[:-window]))) / window
    return ma
