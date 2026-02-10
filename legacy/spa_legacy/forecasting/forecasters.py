from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple

import numpy as np
import pandas as pd


def _get_series(df: pd.DataFrame, y_col: str | None) -> np.ndarray:
    if y_col and y_col in df.columns:
        return df[y_col].astype(float).to_numpy()
    for cand in ("y", "y_raw", "return", "r"):
        if cand in df.columns:
            return df[cand].astype(float).to_numpy()
    raise ValueError("Coluna de target nao encontrada (y/y_raw/return/r).")


def _lag_matrix(values: np.ndarray, n_lags: int) -> Tuple[np.ndarray, np.ndarray]:
    if len(values) <= n_lags:
        return np.empty((0, n_lags)), np.empty((0,))
    X = []
    y = []
    for i in range(n_lags, len(values)):
        X.append(values[i - n_lags : i])
        y.append(values[i])
    return np.asarray(X), np.asarray(y)


def _bootstrap_intervals(pred: np.ndarray, residuals: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    if residuals.size == 0:
        return pred, pred, pred
    q10, q50, q90 = np.quantile(residuals, [0.1, 0.5, 0.9])
    return pred + q10, pred + q50, pred + q90


def _metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    if y_true.size == 0:
        return {"mae": float("nan"), "rmse": float("nan")}
    mae = float(np.mean(np.abs(y_true - y_pred)))
    rmse = float(np.sqrt(np.mean((y_true - y_pred) ** 2)))
    return {"mae": mae, "rmse": rmse}


@dataclass
class BaseForecaster:
    model_name: str = "base"
    model_family: str = "base"
    n_lags: int = 5
    y_col: str | None = None

    def fit(self, train_df: pd.DataFrame) -> "BaseForecaster":
        _ = _get_series(train_df, self.y_col)
        return self

    def predict(self, test_df: pd.DataFrame, horizon: int) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        raise NotImplementedError

    def summarize(self, y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, object]:
        out = {"model_name": self.model_name, "model_family": self.model_family}
        out.update(_metrics(y_true, y_pred))
        return out


class NaivePersistenceForecaster(BaseForecaster):
    model_name = "naive_persistence"
    model_family = "naive"

    def fit(self, train_df: pd.DataFrame) -> "NaivePersistenceForecaster":
        self._train_series = _get_series(train_df, self.y_col)
        return self

    def predict(self, test_df: pd.DataFrame, horizon: int) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        test_series = _get_series(test_df, self.y_col)
        history = list(self._train_series)
        preds = []
        for _ in range(len(test_series)):
            if len(history) < horizon:
                preds.append(float("nan"))
            else:
                preds.append(history[-horizon])
            history.append(test_series[len(preds) - 1])
        pred = np.array(preds, dtype=float)
        residuals = self._train_series[1:] - self._train_series[:-1]
        p10, p50, p90 = _bootstrap_intervals(pred, residuals)
        return pred, p10, p50, p90


class ARIMAForecaster(BaseForecaster):
    model_name = "arima_110"
    model_family = "arima"

    def fit(self, train_df: pd.DataFrame) -> "ARIMAForecaster":
        self._train_series = _get_series(train_df, self.y_col)
        self._model = None
        try:
            from statsmodels.tsa.arima.model import ARIMA
            self._model = ARIMA(self._train_series, order=(1, 0, 0)).fit()
        except Exception:
            self._model = None
        return self

    def predict(self, test_df: pd.DataFrame, horizon: int) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        test_series = _get_series(test_df, self.y_col)
        if self._model is None:
            naive = NaivePersistenceForecaster(y_col=self.y_col)
            naive.fit(pd.DataFrame({"y": self._train_series}))
            return naive.predict(test_df, horizon)

        preds = []
        p10 = []
        p50 = []
        p90 = []
        history = list(self._train_series)
        for _ in range(len(test_series)):
            try:
                from statsmodels.tsa.arima.model import ARIMA

                model = ARIMA(history, order=(1, 0, 0)).fit()
                fc = model.get_forecast(steps=horizon)
                mean = fc.predicted_mean[-1]
                ci = fc.conf_int(alpha=0.2)
                low = ci[-1, 0]
                high = ci[-1, 1]
            except Exception:
                mean = history[-1] if history else float("nan")
                low = mean
                high = mean
            preds.append(mean)
            p10.append(low)
            p50.append(mean)
            p90.append(high)
            history.append(test_series[len(preds) - 1])
        return np.asarray(preds), np.asarray(p10), np.asarray(p50), np.asarray(p90)


class XGBoostForecaster(BaseForecaster):
    model_name = "xgboost"
    model_family = "tree"

    def fit(self, train_df: pd.DataFrame) -> "XGBoostForecaster":
        series = _get_series(train_df, self.y_col)
        X, y = _lag_matrix(series, self.n_lags)
        self._train_series = series
        if X.size == 0:
            self._model = None
            return self
        self._model = None
        try:
            import xgboost as xgb

            self._model = xgb.XGBRegressor(
                n_estimators=200,
                max_depth=3,
                learning_rate=0.05,
                subsample=0.8,
                colsample_bytree=0.8,
                random_state=42,
            )
        except Exception:
            try:
                from sklearn.ensemble import GradientBoostingRegressor

                self._model = GradientBoostingRegressor(random_state=42)
                self.model_name = "gbrt"
            except Exception:
                self._model = None
        if self._model is not None:
            self._model.fit(X, y)
        return self

    def predict(self, test_df: pd.DataFrame, horizon: int) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        test_series = _get_series(test_df, self.y_col)
        if self._model is None:
            naive = NaivePersistenceForecaster(y_col=self.y_col)
            naive.fit(pd.DataFrame({"y": self._train_series}))
            return naive.predict(test_df, horizon)

        history = list(self._train_series)
        preds = []
        for _ in range(len(test_series)):
            if len(history) < self.n_lags:
                preds.append(float("nan"))
            else:
                X = np.asarray(history[-self.n_lags :]).reshape(1, -1)
                pred = float(self._model.predict(X)[0])
                preds.append(pred)
            history.append(test_series[len(preds) - 1])
        pred = np.asarray(preds)
        # residual bootstrap using train fit
        X_train, y_train = _lag_matrix(self._train_series, self.n_lags)
        if X_train.size:
            train_pred = self._model.predict(X_train)
            residuals = y_train - train_pred
        else:
            residuals = np.array([])
        p10, p50, p90 = _bootstrap_intervals(pred, residuals)
        return pred, p10, p50, p90
