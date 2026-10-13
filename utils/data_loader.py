from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
import streamlit as st

from .config import DEFAULT_SAMPLE_ROWS, LARGE_FILE_BYTES, PROJECT_DIR, relative_to_project


@dataclass(frozen=True)
class CsvSummary:
    path: Path
    exists: bool
    size_mb: float
    rows: int | None
    columns: list[str]
    dtypes: dict[str, str]
    error: str | None = None


def _path_key(path: Path | str) -> str:
    return str(Path(path).resolve())


def existing_csvs(*directories: Path) -> list[Path]:
    files: list[Path] = []
    for directory in directories:
        if directory.exists():
            files.extend(sorted(directory.rglob("*.csv")))
    return files


@st.cache_data(show_spinner=False)
def count_csv_rows(path_key: str) -> int | None:
    path = Path(path_key)
    if not path.exists():
        return None
    try:
        with path.open("rb") as handle:
            line_count = sum(chunk.count(b"\n") for chunk in iter(lambda: handle.read(1024 * 1024), b""))
        return max(line_count - 1, 0)
    except OSError:
        return None


@st.cache_data(show_spinner=False)
def read_csv_cached(path_key: str, nrows: int | None = None, usecols: tuple[str, ...] | None = None) -> pd.DataFrame:
    path = Path(path_key)
    kwargs = {"low_memory": False}
    if nrows is not None:
        kwargs["nrows"] = nrows
    if usecols is not None:
        kwargs["usecols"] = list(usecols)
    return pd.read_csv(path, **kwargs)


def read_csv(path: Path, nrows: int | None = None, usecols: Iterable[str] | None = None) -> pd.DataFrame:
    selected_cols = tuple(usecols) if usecols is not None else None
    return read_csv_cached(_path_key(path), nrows=nrows, usecols=selected_cols)


def read_for_display(path: Path, max_rows: int = DEFAULT_SAMPLE_ROWS) -> tuple[pd.DataFrame, bool]:
    if not path.exists():
        return pd.DataFrame(), False
    is_sampled = path.stat().st_size > LARGE_FILE_BYTES
    return read_csv(path, nrows=max_rows if is_sampled else None), is_sampled


def read_schema(path: Path, sample_rows: int = 500) -> tuple[list[str], dict[str, str], str | None]:
    if not path.exists():
        return [], {}, "File is missing."
    try:
        df = read_csv(path, nrows=sample_rows)
        return list(df.columns), {column: str(dtype) for column, dtype in df.dtypes.items()}, None
    except Exception as exc:  # noqa: BLE001 - surfaced to the dashboard.
        return [], {}, f"{type(exc).__name__}: {exc}"


def summarize_csv(path: Path, count_rows: bool = False) -> CsvSummary:
    exists = path.exists()
    if not exists:
        return CsvSummary(path, False, 0.0, None, [], {}, "File is missing.")
    columns, dtypes, error = read_schema(path)
    rows = count_csv_rows(_path_key(path)) if count_rows and error is None else None
    return CsvSummary(
        path=path,
        exists=True,
        size_mb=path.stat().st_size / (1024 * 1024),
        rows=rows,
        columns=columns,
        dtypes=dtypes,
        error=error,
    )


def build_availability_table(named_paths: dict[str, Path], include_rows: bool = False) -> pd.DataFrame:
    records = []
    for name, path in named_paths.items():
        summary = summarize_csv(path, count_rows=include_rows and path.stat().st_size < LARGE_FILE_BYTES if path.exists() else False)
        records.append(
            {
                "Dataset": name,
                "Path": relative_to_project(path),
                "Available": summary.exists,
                "Size MB": round(summary.size_mb, 2),
                "Rows": summary.rows,
                "Columns": len(summary.columns),
                "Schema error": summary.error,
            }
        )
    return pd.DataFrame(records)


def quality_summary(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["Column", "Type", "Missing", "Missing %", "Infinite", "Unique"])
    rows = []
    for column in df.columns:
        series = df[column]
        numeric = pd.to_numeric(series, errors="coerce") if not pd.api.types.is_numeric_dtype(series) else series
        infinite = int(np.isinf(numeric.to_numpy(dtype=float, na_value=np.nan)).sum()) if pd.api.types.is_numeric_dtype(numeric) else 0
        rows.append(
            {
                "Column": column,
                "Type": str(series.dtype),
                "Missing": int(series.isna().sum()),
                "Missing %": round(float(series.isna().mean() * 100), 2),
                "Infinite": infinite,
                "Unique": int(series.nunique(dropna=True)),
            }
        )
    return pd.DataFrame(rows)


def dataframe_download(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8")


def safe_unique(df: pd.DataFrame, column: str, limit: int | None = None) -> list:
    if column not in df.columns:
        return []
    values = df[column].dropna().unique().tolist()
    values = sorted(values)
    return values[:limit] if limit is not None else values


def sample_for_plot(df: pd.DataFrame, max_points: int) -> pd.DataFrame:
    if len(df) <= max_points:
        return df
    return df.iloc[np.linspace(0, len(df) - 1, max_points).astype(int)]


def numeric_columns(df: pd.DataFrame) -> list[str]:
    return [column for column in df.columns if pd.api.types.is_numeric_dtype(df[column])]


def all_project_csvs() -> list[Path]:
    candidates = [PROJECT_DIR / name for name in ("charge.csv", "discharge.csv", "impedance.csv", "meta.csv")]
    candidates.extend(existing_csvs(PROJECT_DIR / "data", PROJECT_DIR / "outputs", PROJECT_DIR / "model_results"))
    seen: set[str] = set()
    unique: list[Path] = []
    for path in candidates:
        key = str(path.resolve())
        if path.exists() and key not in seen:
            unique.append(path)
            seen.add(key)
    return unique

