import numpy as np


def embed(series, tau, m):
    series = np.asarray(series, dtype=float)
    start = (m - 1) * tau
    X = []
    y = []
    idx = []
    for i in range(start, len(series) - 1):
        X.append([series[i - j * tau] for j in range(m)])
        y.append(series[i + 1])
        idx.append(i + 1)
    if not X:
        return None, None, None
    return np.array(X), np.array(y), np.array(idx)


class TakensKNN:
    def __init__(self, tau=2, m=4, k=10):
        self.tau = tau
        self.m = m
        self.k = k
        self.mean_ = None
        self.std_ = None
        self.X_train_ = None
        self.y_train_ = None

    def fit(self, series, train_idx):
        X, y, idx = embed(series, self.tau, self.m)
        if X is None:
            return False
        mask = idx <= train_idx
        X_train = X[mask]
        y_train = y[mask]
        if len(X_train) < self.k:
            return False
        mean = X_train.mean(axis=0)
        std = X_train.std(axis=0)
        std[std == 0] = 1.0
        self.mean_ = mean
        self.std_ = std
        self.X_train_ = (X_train - mean) / std
        self.y_train_ = y_train
        return True

    def predict_1step(self, x_query):
        if self.X_train_ is None:
            return None
        xq = (np.asarray(x_query, dtype=float) - self.mean_) / self.std_
        dists = np.linalg.norm(self.X_train_ - xq, axis=1)
        idx = np.argpartition(dists, self.k - 1)[: self.k]
        weights = 1.0 / (dists[idx] + 1e-6)
        return float(np.sum(self.y_train_[idx] * weights) / np.sum(weights))

    def predict_multistep(self, series, start_index, H):
        state = np.array([series[start_index - j * self.tau] for j in range(self.m)], dtype=float)
        preds = []
        for _ in range(H):
            next_val = self.predict_1step(state)
            if next_val is None:
                break
            preds.append(next_val)
            state = np.concatenate([[next_val], state[:-1]])
        return np.array(preds)
