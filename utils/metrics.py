from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.metrics import explained_variance_score, mean_absolute_error, mean_squared_error, r2_score


def valid_pairs(actual: pd.Series, predicted: pd.Series) -> tuple[np.ndarray, np.ndarray]:
    frame = pd.DataFrame({"actual": pd.to_numeric(actual, errors="coerce"), "predicted": pd.to_numeric(predicted, errors="coerce")})
    frame = frame.replace([np.inf, -np.inf], np.nan).dropna()
    return frame["actual"].to_numpy(), frame["predicted"].to_numpy()


def regression_metrics(actual: pd.Series, predicted: pd.Series, mape_floor: float = 1e-8) -> dict[str, float | int | None]:
    y_true, y_pred = valid_pairs(actual, predicted)
    n_obs = int(len(y_true))
    if n_obs == 0:
        return {"n": 0, "MAE": None, "MSE": None, "RMSE": None, "R2": None, "Explained Variance": None, "Max Absolute Error": None, "Mean Error": None, "MAPE": None}

    errors = y_true - y_pred
    mse = mean_squared_error(y_true, y_pred)
    nonzero = np.abs(y_true) > mape_floor
    mape = float(np.mean(np.abs(errors[nonzero] / y_true[nonzero])) * 100) if nonzero.any() else None
    r2 = None if n_obs < 2 else float(r2_score(y_true, y_pred))
    evs = None if n_obs < 2 else float(explained_variance_score(y_true, y_pred))
    return {
        "n": n_obs,
        "MAE": float(mean_absolute_error(y_true, y_pred)),
        "MSE": float(mse),
        "RMSE": float(np.sqrt(mse)),
        "R2": r2,
        "Explained Variance": evs,
        "Max Absolute Error": float(np.max(np.abs(errors))),
        "Mean Error": float(np.mean(errors)),
        "MAPE": mape,
    }


def metrics_frame(df: pd.DataFrame, actual_col: str, prediction_cols: dict[str, str]) -> pd.DataFrame:
    rows = []
    for model, column in prediction_cols.items():
        if actual_col in df.columns and column in df.columns:
            row = {"Model": model, "Actual": actual_col, "Prediction": column}
            row.update(regression_metrics(df[actual_col], df[column]))
            rows.append(row)
    return pd.DataFrame(rows)

