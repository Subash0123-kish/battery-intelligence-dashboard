from __future__ import annotations

import pandas as pd


def first_existing(columns: list[str], candidates: list[str]) -> str | None:
    lookup = {column.lower(): column for column in columns}
    for candidate in candidates:
        if candidate.lower() in lookup:
            return lookup[candidate.lower()]
    return None


def prediction_columns(df: pd.DataFrame, prefixes: tuple[str, ...] = ("predicted", "prediction")) -> list[str]:
    cols = []
    for column in df.columns:
        lower = column.lower()
        if any(lower.startswith(prefix) for prefix in prefixes):
            cols.append(column)
    return cols


def residual_columns(df: pd.DataFrame) -> list[str]:
    return [column for column in df.columns if "residual" in column.lower() or "error" in column.lower()]


def missing_columns(df: pd.DataFrame, required: list[str]) -> list[str]:
    return [column for column in required if column not in df.columns]

