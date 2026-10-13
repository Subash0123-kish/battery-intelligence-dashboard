from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st

from .config import PLOT_SAMPLE_POINTS
from .data_loader import dataframe_download, numeric_columns, sample_for_plot
from .plotting import ACCENT, BLUE, NAVY, ORANGE


@dataclass
class SchemaDiff:
    common_columns: list[str]
    baseline_only_columns: list[str]
    comparison_only_columns: list[str]
    dtype_mismatches: dict[str, tuple[str, str]]


def compare_schemas(df_base: pd.DataFrame, df_comp: pd.DataFrame) -> SchemaDiff:
    base_cols = list(df_base.columns)
    comp_cols = list(df_comp.columns)
    base_set = set(base_cols)
    comp_set = set(comp_cols)

    common = [c for c in base_cols if c in comp_set]
    base_only = [c for c in base_cols if c not in comp_set]
    comp_only = [c for c in comp_cols if c not in base_set]

    mismatches: dict[str, tuple[str, str]] = {}
    for col in common:
        t_base = str(df_base[col].dtype)
        t_comp = str(df_comp[col].dtype)
        if t_base != t_comp:
            mismatches[col] = (t_base, t_comp)

    return SchemaDiff(
        common_columns=common,
        baseline_only_columns=base_only,
        comparison_only_columns=comp_only,
        dtype_mismatches=mismatches,
    )


def compare_numeric_stats(df_base: pd.DataFrame, df_comp: pd.DataFrame, columns: list[str] | None = None) -> pd.DataFrame:
    if columns is None:
        base_numeric = set(numeric_columns(df_base))
        comp_numeric = set(numeric_columns(df_comp))
        columns = sorted(list(base_numeric.intersection(comp_numeric)))

    records: list[dict[str, Any]] = []
    for col in columns:
        s_base = pd.to_numeric(df_base[col], errors="coerce")
        s_comp = pd.to_numeric(df_comp[col], errors="coerce")

        b_count = int(s_base.notna().sum())
        c_count = int(s_comp.notna().sum())
        b_mean = float(s_base.mean()) if b_count > 0 else np.nan
        c_mean = float(s_comp.mean()) if c_count > 0 else np.nan
        mean_diff = c_mean - b_mean if not (np.isnan(b_mean) or np.isnan(c_mean)) else np.nan
        pct_change = (mean_diff / b_mean * 100.0) if not (np.isnan(mean_diff) or b_mean == 0) else np.nan

        b_std = float(s_base.std()) if b_count > 1 else np.nan
        c_std = float(s_comp.std()) if c_count > 1 else np.nan

        b_min = float(s_base.min()) if b_count > 0 else np.nan
        c_min = float(s_comp.min()) if c_count > 0 else np.nan

        b_max = float(s_base.max()) if b_count > 0 else np.nan
        c_max = float(s_comp.max()) if c_count > 0 else np.nan

        b_null = int(s_base.isna().sum())
        c_null = int(s_comp.isna().sum())

        records.append(
            {
                "Column": col,
                "Base Mean": round(b_mean, 4) if not np.isnan(b_mean) else None,
                "Comp Mean": round(c_mean, 4) if not np.isnan(c_mean) else None,
                "Mean Diff (Δ)": round(mean_diff, 4) if not np.isnan(mean_diff) else None,
                "Mean % Change": f"{pct_change:+.2f}%" if not np.isnan(pct_change) else "N/A",
                "Base Std": round(b_std, 4) if not np.isnan(b_std) else None,
                "Comp Std": round(c_std, 4) if not np.isnan(c_std) else None,
                "Base Min": round(b_min, 4) if not np.isnan(b_min) else None,
                "Comp Min": round(c_min, 4) if not np.isnan(c_min) else None,
                "Base Max": round(b_max, 4) if not np.isnan(b_max) else None,
                "Comp Max": round(c_max, 4) if not np.isnan(c_max) else None,
                "Base Nulls": b_null,
                "Comp Nulls": c_null,
                "Nulls Diff (Δ)": c_null - b_null,
            }
        )

    return pd.DataFrame(records)


def find_cell_differences(
    df_base: pd.DataFrame,
    df_comp: pd.DataFrame,
    key_col: str | None = None,
    max_diffs: int = 2000,
) -> tuple[pd.DataFrame, int, list[Any], list[Any]]:
    common_cols = [c for c in df_base.columns if c in df_comp.columns]
    if not common_cols:
        return pd.DataFrame(), 0, [], []

    keys_base_only: list[Any] = []
    keys_comp_only: list[Any] = []

    if key_col and key_col in common_cols:
        # Deduplicate on key for reliable alignment
        b_keyed = df_base.drop_duplicates(subset=[key_col]).set_index(key_col)
        c_keyed = df_comp.drop_duplicates(subset=[key_col]).set_index(key_col)

        b_keys = set(b_keyed.index)
        c_keys = set(c_keyed.index)

        keys_base_only = sorted(list(b_keys - c_keys))[:100]
        keys_comp_only = sorted(list(c_keys - b_keys))[:100]

        shared_keys = [k for k in b_keyed.index if k in c_keys]
        compare_cols = [c for c in common_cols if c != key_col]

        b_sub = b_keyed.loc[shared_keys, compare_cols]
        c_sub = c_keyed.loc[shared_keys, compare_cols]
        index_label = key_col
    else:
        # Compare by row index up to min length
        min_len = min(len(df_base), len(df_comp))
        b_sub = df_base.iloc[:min_len][common_cols]
        c_sub = df_comp.iloc[:min_len][common_cols]
        shared_keys = list(range(min_len))
        compare_cols = common_cols
        index_label = "Row Index"
        if len(df_base) > min_len:
            keys_base_only = [f"Row {i}" for i in range(min_len, min(len(df_base), min_len + 50))]
        if len(df_comp) > min_len:
            keys_comp_only = [f"Row {i}" for i in range(min_len, min(len(df_comp), min_len + 50))]

    diff_records: list[dict[str, Any]] = []
    total_diff_count = 0

    for col in compare_cols:
        b_vals = b_sub[col]
        c_vals = c_sub[col]

        # Check equality handling nulls
        both_na = b_vals.isna() & c_vals.isna()
        is_num = pd.api.types.is_numeric_dtype(b_vals) and pd.api.types.is_numeric_dtype(c_vals)

        if is_num:
            # Floating tolerance
            not_eq = ~both_na & ((b_vals.isna() != c_vals.isna()) | ~np.isclose(b_vals.fillna(0), c_vals.fillna(0), equal_nan=True))
        else:
            not_eq = ~both_na & (b_vals.astype(str) != c_vals.astype(str))

        diff_indices = b_sub.index[not_eq].tolist()
        total_diff_count += len(diff_indices)

        for idx in diff_indices:
            if len(diff_records) < max_diffs:
                bv = b_vals.loc[idx]
                cv = c_vals.loc[idx]
                delta_val: Any = None
                if is_num and pd.notna(bv) and pd.notna(cv):
                    try:
                        delta_val = round(float(cv) - float(bv), 4)
                    except Exception:
                        delta_val = None
                diff_records.append(
                    {
                        index_label: idx,
                        "Column": col,
                        "Base Value": bv,
                        "Comp Value": cv,
                        "Difference (Δ)": delta_val,
                    }
                )

    diff_df = pd.DataFrame(diff_records)
    return diff_df, total_diff_count, keys_base_only, keys_comp_only


def plot_diff_distribution(
    df_base: pd.DataFrame,
    df_comp: pd.DataFrame,
    column: str,
    base_label: str = "Baseline",
    comp_label: str = "Uploaded",
):
    fig, ax = plt.subplots(figsize=(9, 4.6))
    s_base = pd.to_numeric(df_base[column], errors="coerce").dropna()
    s_comp = pd.to_numeric(df_comp[column], errors="coerce").dropna()

    if s_base.empty and s_comp.empty:
        ax.set_title(f"No numeric data available for {column}", loc="left", color=NAVY)
        return fig

    # Sample if large
    if len(s_base) > PLOT_SAMPLE_POINTS:
        s_base = s_base.sample(PLOT_SAMPLE_POINTS, random_state=42)
    if len(s_comp) > PLOT_SAMPLE_POINTS:
        s_comp = s_comp.sample(PLOT_SAMPLE_POINTS, random_state=42)

    # Determine common range
    all_vals = np.concatenate([s_base.to_numpy(), s_comp.to_numpy()])
    min_v, max_v = float(np.nanmin(all_vals)), float(np.nanmax(all_vals))
    bins = np.linspace(min_v, max_v, 35)

    if not s_base.empty:
        ax.hist(s_base, bins=bins, alpha=0.55, color=ACCENT, label=f"{base_label} (Mean: {s_base.mean():.2f})", edgecolor="white")
        ax.axvline(s_base.mean(), color=ACCENT, linestyle="--", linewidth=1.5)
    if not s_comp.empty:
        ax.hist(s_comp, bins=bins, alpha=0.55, color=ORANGE, label=f"{comp_label} (Mean: {s_comp.mean():.2f})", edgecolor="white")
        ax.axvline(s_comp.mean(), color=ORANGE, linestyle="--", linewidth=1.5)

    ax.set_title(f"Distribution Comparison: {column}", loc="left", fontsize=12, color=NAVY)
    ax.set_xlabel(column)
    ax.set_ylabel("Count")
    ax.grid(True, axis="y", alpha=0.25)
    ax.legend(frameon=True)
    fig.tight_layout()
    return fig


def render_diff_view(
    df_base: pd.DataFrame,
    df_comp: pd.DataFrame,
    base_name: str = "Baseline Dataset",
    comp_name: str = "Uploaded CSV",
):
    """Full interactive Streamlit component rendering differences between two datasets."""
    schema_diff = compare_schemas(df_base, df_comp)

    # Key metric deltas
    row_delta = len(df_comp) - len(df_base)
    col_delta = len(df_comp.columns) - len(df_base.columns)
    base_nulls = int(df_base.isna().sum().sum())
    comp_nulls = int(df_comp.isna().sum().sum())
    null_delta = comp_nulls - base_nulls
    base_dups = int(df_base.duplicated().sum())
    comp_dups = int(df_comp.duplicated().sum())

    st.markdown(f"#### Comparison: **{base_name}** vs **{comp_name}**")

    # High-level metrics row
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric(
            "Rows",
            f"{len(df_comp):,}",
            delta=f"{row_delta:+,} rows" if row_delta != 0 else "Identical row count",
            delta_color="normal",
            border=True,
        )
    with m2:
        st.metric(
            "Columns",
            len(df_comp.columns),
            delta=f"{col_delta:+,} cols" if col_delta != 0 else "Identical col count",
            delta_color="normal",
            border=True,
        )
    with m3:
        st.metric(
            "Missing cells",
            f"{comp_nulls:,}",
            delta=f"{null_delta:+,} cells" if null_delta != 0 else "No difference",
            delta_color="inverse",
            border=True,
        )
    with m4:
        st.metric(
            "Duplicate rows",
            f"{comp_dups:,}",
            delta=f"{comp_dups - base_dups:+,} dups" if (comp_dups - base_dups) != 0 else "Same duplicate count",
            delta_color="inverse",
            border=True,
        )

    # Sub tabs for detailed diff views
    diff_tabs = st.tabs(
        [
            "Schema & Columns",
            "Statistical Differences",
            "Cell / Row Differences",
            "Visual Distribution",
            "Side-by-Side Preview",
        ]
    )

    # TAB 1: Schema
    with diff_tabs[0]:
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(f"**:green-badge[Common columns ({len(schema_diff.common_columns)})]**")
            st.dataframe(pd.DataFrame({"Column": schema_diff.common_columns}), height=220, width="stretch", hide_index=True)
        with c2:
            st.markdown(f"**:orange-badge[Baseline only / Removed ({len(schema_diff.baseline_only_columns)})]**")
            if schema_diff.baseline_only_columns:
                st.dataframe(pd.DataFrame({"Removed Column": schema_diff.baseline_only_columns}), height=220, width="stretch", hide_index=True)
            else:
                st.info("No columns were removed from the baseline.")
        with c3:
            st.markdown(f"**:blue-badge[Uploaded only / Added ({len(schema_diff.comparison_only_columns)})]**")
            if schema_diff.comparison_only_columns:
                st.dataframe(pd.DataFrame({"Added Column": schema_diff.comparison_only_columns}), height=220, width="stretch", hide_index=True)
            else:
                st.info("No new columns were added in the uploaded file.")

        if schema_diff.dtype_mismatches:
            st.warning("Data type mismatches detected across shared columns:")
            mismatch_df = pd.DataFrame(
                [{"Column": col, f"{base_name} Type": types[0], f"{comp_name} Type": types[1]} for col, types in schema_diff.dtype_mismatches.items()]
            )
            st.dataframe(mismatch_df, width="stretch", hide_index=True)

    # TAB 2: Statistical Differences
    with diff_tabs[1]:
        shared_numeric = sorted(list(set(numeric_columns(df_base)).intersection(set(numeric_columns(df_comp)))))
        if shared_numeric:
            stat_df = compare_numeric_stats(df_base, df_comp, shared_numeric)
            st.markdown("**Summary statistics comparison for shared numeric columns:**")
            st.dataframe(stat_df, width="stretch", hide_index=True)
            st.download_button(
                "Download statistical diff report (CSV)",
                data=dataframe_download(stat_df),
                file_name="statistical_difference_report.csv",
                mime="text/csv",
                key=f"dl_stat_diff_{base_name}_{comp_name}",
            )
        else:
            st.info("No common numeric columns found to compute statistical differences.")

    # TAB 3: Cell / Row Differences
    with diff_tabs[2]:
        st.markdown("**Inspect cell and row-level value changes:**")
        key_options = ["(Compare by Row Index)"] + schema_diff.common_columns
        selected_key = st.selectbox("Align records by key / ID column", key_options, index=0, key=f"key_select_{base_name}_{comp_name}")
        actual_key = None if selected_key == "(Compare by Row Index)" else selected_key

        diff_df, total_diff_count, base_only_keys, comp_only_keys = find_cell_differences(
            df_base, df_comp, key_col=actual_key, max_diffs=1000
        )

        col_k1, col_k2 = st.columns(2)
        with col_k1:
            st.write(f"Total modified cell values detected: **{total_diff_count:,}**")
        with col_k2:
            if base_only_keys:
                st.caption(f"Keys/Rows only in baseline (first {len(base_only_keys)}): {base_only_keys[:5]}...")
            if comp_only_keys:
                st.caption(f"Keys/Rows only in uploaded (first {len(comp_only_keys)}): {comp_only_keys[:5]}...")

        if not diff_df.empty:
            filter_col = st.selectbox(
                "Filter cell diffs by column",
                ["All differing columns"] + sorted(diff_df["Column"].unique().tolist()),
                key=f"filt_col_{base_name}_{comp_name}",
            )
            display_diff = diff_df if filter_col == "All differing columns" else diff_df[diff_df["Column"] == filter_col]
            st.dataframe(display_diff.head(500), width="stretch", hide_index=True)
            st.download_button(
                "Download cell differences (CSV)",
                data=dataframe_download(diff_df),
                file_name="cell_differences_report.csv",
                mime="text/csv",
                key=f"dl_cell_diff_{base_name}_{comp_name}",
            )
        elif total_diff_count == 0:
            st.success("All aligned cell values across common columns are completely identical!")

    # TAB 4: Visual Distribution
    with diff_tabs[3]:
        shared_numeric = sorted(list(set(numeric_columns(df_base)).intersection(set(numeric_columns(df_comp)))))
        if shared_numeric:
            plot_col = st.selectbox("Select column to compare distribution", shared_numeric, key=f"plot_col_{base_name}_{comp_name}")
            fig = plot_diff_distribution(df_base, df_comp, plot_col, base_label=base_name, comp_label=comp_name)
            st.pyplot(fig)
        else:
            st.info("No common numeric columns available to chart.")

    # TAB 5: Side-by-side Preview
    with diff_tabs[4]:
        p_left, p_right = st.columns(2)
        with p_left:
            st.markdown(f"**{base_name} (First 100 rows)**")
            st.dataframe(df_base.head(100), height=380, width="stretch", hide_index=True)
        with p_right:
            st.markdown(f"**{comp_name} (First 100 rows)**")
            st.dataframe(df_comp.head(100), height=380, width="stretch", hide_index=True)
