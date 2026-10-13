from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .config import PLOT_SAMPLE_POINTS
from .data_loader import sample_for_plot


ACCENT = "#0f766e"
NAVY = "#172554"
BLUE = "#2563eb"
ORANGE = "#ea580c"
GRAY = "#64748b"


def _numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce")


def line_chart(df: pd.DataFrame, x: str, y_columns: list[str], title: str, y_label: str | None = None):
    plot_df = sample_for_plot(df.dropna(subset=[x]), PLOT_SAMPLE_POINTS)
    fig, ax = plt.subplots(figsize=(9, 4.8))
    colors = [ACCENT, BLUE, ORANGE, "#7c3aed", "#be123c"]
    for idx, column in enumerate(y_columns):
        if column in plot_df.columns:
            frame = plot_df[[x, column]].copy()
            frame[x] = _numeric(frame[x])
            frame[column] = _numeric(frame[column])
            frame = frame.dropna()
            if not frame.empty:
                ax.plot(frame[x], frame[column], label=column, linewidth=1.7, color=colors[idx % len(colors)])
    ax.set_title(title, loc="left", fontsize=12, color=NAVY)
    ax.set_xlabel(x)
    ax.set_ylabel(y_label or ", ".join(y_columns))
    ax.grid(True, alpha=0.25)
    if len(y_columns) > 1:
        ax.legend()
    fig.tight_layout()
    return fig


def scatter_actual_pred(df: pd.DataFrame, actual: str, predicted: str, title: str):
    plot_df = sample_for_plot(df[[actual, predicted]].copy(), PLOT_SAMPLE_POINTS)
    plot_df[actual] = _numeric(plot_df[actual])
    plot_df[predicted] = _numeric(plot_df[predicted])
    plot_df = plot_df.dropna()
    fig, ax = plt.subplots(figsize=(6.8, 5.2))
    if not plot_df.empty:
        ax.scatter(plot_df[actual], plot_df[predicted], s=12, alpha=0.45, color=ACCENT)
        lower = float(np.nanmin([plot_df[actual].min(), plot_df[predicted].min()]))
        upper = float(np.nanmax([plot_df[actual].max(), plot_df[predicted].max()]))
        ax.plot([lower, upper], [lower, upper], color=ORANGE, linewidth=1.4, label="y = x")
        ax.legend()
    ax.set_title(title, loc="left", fontsize=12, color=NAVY)
    ax.set_xlabel(actual)
    ax.set_ylabel(predicted)
    ax.grid(True, alpha=0.25)
    fig.tight_layout()
    return fig


def residual_plot(df: pd.DataFrame, predicted: str, residual: str, title: str):
    plot_df = sample_for_plot(df[[predicted, residual]].copy(), PLOT_SAMPLE_POINTS)
    plot_df[predicted] = _numeric(plot_df[predicted])
    plot_df[residual] = _numeric(plot_df[residual])
    plot_df = plot_df.dropna()
    fig, ax = plt.subplots(figsize=(8, 4.6))
    if not plot_df.empty:
        ax.scatter(plot_df[predicted], plot_df[residual], s=12, alpha=0.45, color=BLUE)
        ax.axhline(0, color=ORANGE, linewidth=1.2)
    ax.set_title(title, loc="left", fontsize=12, color=NAVY)
    ax.set_xlabel(predicted)
    ax.set_ylabel(residual)
    ax.grid(True, alpha=0.25)
    fig.tight_layout()
    return fig


def histogram(df: pd.DataFrame, column: str, title: str, x_label: str | None = None):
    values = _numeric(df[column]).replace([np.inf, -np.inf], np.nan).dropna() if column in df.columns else pd.Series(dtype=float)
    fig, ax = plt.subplots(figsize=(8, 4.5))
    if not values.empty:
        ax.hist(values, bins=40, color=ACCENT, alpha=0.82, edgecolor="white")
    ax.set_title(title, loc="left", fontsize=12, color=NAVY)
    ax.set_xlabel(x_label or column)
    ax.set_ylabel("Count")
    ax.grid(True, axis="y", alpha=0.25)
    fig.tight_layout()
    return fig


def bar_chart(df: pd.DataFrame, x: str, y: str, title: str, y_label: str | None = None):
    plot_df = df[[x, y]].dropna().copy()
    plot_df[y] = _numeric(plot_df[y])
    plot_df = plot_df.dropna()
    fig, ax = plt.subplots(figsize=(8.5, 4.6))
    if not plot_df.empty:
        ax.bar(plot_df[x].astype(str), plot_df[y], color=ACCENT)
        ax.tick_params(axis="x", rotation=25)
    ax.set_title(title, loc="left", fontsize=12, color=NAVY)
    ax.set_xlabel(x)
    ax.set_ylabel(y_label or y)
    ax.grid(True, axis="y", alpha=0.25)
    fig.tight_layout()
    return fig

