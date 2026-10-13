import io
from pathlib import Path

import pandas as pd
import streamlit as st

from utils.config import DEFAULT_SAMPLE_ROWS, KEY_OUTPUTS, PROCESSED_DATASETS, SOURCE_DATASETS, relative_to_project
from utils.data_loader import read_for_display
from utils.diff import render_diff_view
from utils.ui import apply_theme, info_panel, page_intro, sidebar_status


apply_theme()
sidebar_status()
page_intro(
    "CSV Comparison & Difference Viewer",
    "Upload CSV files to inspect structural schemas, summary statistics, distribution shifts, and cell-level differences.",
    icon=":material/difference:",
)

all_workspace_datasets = {**SOURCE_DATASETS, **PROCESSED_DATASETS, **KEY_OUTPUTS}

st.markdown(
    """
    Compare an uploaded CSV against any workspace dataset or upload two arbitrary CSV files
    to see comprehensive differences in row/column counts, schemas, statistical metrics, distributions, and individual cell values.
    """
)

comparison_mode = st.radio(
    "Comparison mode",
    [
        "Upload CSV vs Workspace Dataset",
        "Upload Two CSV Files (Baseline vs Comparison)",
        "Compare Two Workspace Datasets",
    ],
    horizontal=True,
)

df_baseline = None
df_comparison = None
baseline_label = "Baseline"
comparison_label = "Comparison"

if comparison_mode == "Upload CSV vs Workspace Dataset":
    col_left, col_right = st.columns(2)
    with col_left:
        st.subheader("1. Baseline Workspace Dataset", icon=":material/database:")
        selected_ws_name = st.selectbox("Select workspace dataset", list(all_workspace_datasets.keys()))
        ws_path = all_workspace_datasets[selected_ws_name]
        if not ws_path.exists():
            st.error(f"Selected file not found on disk: {relative_to_project(ws_path)}")
        else:
            baseline_label = selected_ws_name
            with st.spinner("Loading baseline dataset..."):
                df_baseline, is_sampled = read_for_display(ws_path, max_rows=DEFAULT_SAMPLE_ROWS)
            st.caption(f"{relative_to_project(ws_path)} | {len(df_baseline):,} rows loaded, {len(df_baseline.columns)} cols")
            if is_sampled:
                st.info(f"Sampled first {len(df_baseline):,} rows for comparison performance.")

    with col_right:
        st.subheader("2. Upload CSV File", icon=":material/upload_file:")
        uploaded_file = st.file_uploader(
            "Upload CSV file to compare",
            type=["csv"],
            key="diff_upload_single",
            help="Select a CSV file from your computer to compare against the baseline dataset.",
        )
        if uploaded_file is not None:
            comparison_label = uploaded_file.name
            try:
                with st.spinner("Reading uploaded CSV..."):
                    df_comparison = pd.read_csv(uploaded_file, low_memory=False)
                st.caption(f"{uploaded_file.name} | {len(df_comparison):,} rows loaded, {len(df_comparison.columns)} cols")
            except Exception as exc:
                st.error(f"Error parsing uploaded CSV: {exc}")
        else:
            st.info("Please upload a CSV file using the button above to begin difference analysis.")

elif comparison_mode == "Upload Two CSV Files (Baseline vs Comparison)":
    col_left, col_right = st.columns(2)
    with col_left:
        st.subheader("1. Baseline CSV File", icon=":material/upload_file:")
        uploaded_base = st.file_uploader(
            "Upload Baseline CSV",
            type=["csv"],
            key="diff_upload_base",
            help="Upload the reference/baseline CSV file.",
        )
        if uploaded_base is not None:
            baseline_label = f"Baseline ({uploaded_base.name})"
            try:
                with st.spinner("Reading baseline CSV..."):
                    df_baseline = pd.read_csv(uploaded_base, low_memory=False)
                st.caption(f"{uploaded_base.name} | {len(df_baseline):,} rows, {len(df_baseline.columns)} cols")
            except Exception as exc:
                st.error(f"Error parsing baseline CSV: {exc}")
        else:
            st.info("Upload the baseline CSV file.")

    with col_right:
        st.subheader("2. Comparison CSV File", icon=":material/upload_file:")
        uploaded_comp = st.file_uploader(
            "Upload Comparison CSV",
            type=["csv"],
            key="diff_upload_comp",
            help="Upload the modified or newer CSV file to compare against the baseline.",
        )
        if uploaded_comp is not None:
            comparison_label = f"Uploaded ({uploaded_comp.name})"
            try:
                with st.spinner("Reading comparison CSV..."):
                    df_comparison = pd.read_csv(uploaded_comp, low_memory=False)
                st.caption(f"{uploaded_comp.name} | {len(df_comparison):,} rows, {len(df_comparison.columns)} cols")
            except Exception as exc:
                st.error(f"Error parsing comparison CSV: {exc}")
        else:
            st.info("Upload the comparison CSV file.")

else:  # Compare Two Workspace Datasets
    col_left, col_right = st.columns(2)
    dataset_keys = list(all_workspace_datasets.keys())
    with col_left:
        st.subheader("1. Baseline Dataset", icon=":material/database:")
        selected_b = st.selectbox("Select baseline dataset", dataset_keys, index=0)
        path_b = all_workspace_datasets[selected_b]
        if path_b.exists():
            baseline_label = selected_b
            df_baseline, _ = read_for_display(path_b, max_rows=DEFAULT_SAMPLE_ROWS)
            st.caption(f"{relative_to_project(path_b)} | {len(df_baseline):,} rows, {len(df_baseline.columns)} cols")
        else:
            st.error(f"Dataset not found: {relative_to_project(path_b)}")

    with col_right:
        st.subheader("2. Comparison Dataset", icon=":material/database:")
        selected_c = st.selectbox("Select comparison dataset", dataset_keys, index=min(1, len(dataset_keys) - 1))
        path_c = all_workspace_datasets[selected_c]
        if path_c.exists():
            comparison_label = selected_c
            df_comparison, _ = read_for_display(path_c, max_rows=DEFAULT_SAMPLE_ROWS)
            st.caption(f"{relative_to_project(path_c)} | {len(df_comparison):,} rows, {len(df_comparison.columns)} cols")
        else:
            st.error(f"Dataset not found: {relative_to_project(path_c)}")

st.divider()

if df_baseline is not None and df_comparison is not None:
    render_diff_view(
        df_base=df_baseline,
        df_comp=df_comparison,
        base_name=baseline_label,
        comp_name=comparison_label,
    )
else:
    info_panel(
        "💡 <strong>Ready to compare:</strong> Use the upload button(s) above to provide CSV data. "
        "The tool will automatically calculate differences across column schemas, data types, "
        "summary statistics (mean, std, min, max, nulls), distribution shifts, and cell values."
    )
