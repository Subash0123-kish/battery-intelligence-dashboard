from pathlib import Path

import pandas as pd
import streamlit as st

from utils.config import DEFAULT_SAMPLE_ROWS, PROCESSED_DATASETS, SOURCE_DATASETS, relative_to_project
from utils.data_loader import dataframe_download, numeric_columns, quality_summary, read_for_display, safe_unique, summarize_csv
from utils.diff import render_diff_view
from utils.plotting import histogram, line_chart
from utils.ui import apply_theme, info_panel, integrity_warning, page_intro, sidebar_status


apply_theme()
sidebar_status()
page_intro("Dataset explorer", "Interactive inspection of source and processed CSV files.", icon=":material/database:")

dataset_paths = {**SOURCE_DATASETS, **PROCESSED_DATASETS}
dataset_options = list(dataset_paths.keys()) + ["📁 Upload custom CSV..."]
selected_name = st.selectbox("Dataset", dataset_options)

if selected_name == "📁 Upload custom CSV...":
    uploaded_file = st.file_uploader("Upload CSV file to explore", type=["csv"], key="explorer_custom_csv")
    if uploaded_file is None:
        info_panel("Please upload a CSV file above to explore its schema, records, quality, and charts.")
        st.stop()
    try:
        df = pd.read_csv(uploaded_file, low_memory=False)
    except Exception as exc:
        st.error(f"Failed to read CSV file: {exc}")
        st.stop()
    summary_cols = list(df.columns)
    summary_dtypes = {c: str(df[c].dtype) for c in df.columns}
    st.caption(f"Uploaded file: {uploaded_file.name} | {len(df):,} rows, {len(df.columns)} columns")
    sampled = False
    path_stem = Path(uploaded_file.name).stem
else:
    path = dataset_paths[selected_name]
    summary = summarize_csv(path, count_rows=False)
    if not summary.exists:
        st.warning(f"Dataset '{selected_name}' ({relative_to_project(path)}) is not hosted in this online repository (exceeds cloud storage limits). You can select '📁 Upload custom CSV...' from the dropdown above to inspect your own file.")
        st.stop()
    if summary.error:
        st.error(summary.error)
        st.stop()
    st.caption(f"{relative_to_project(path)} | {summary.size_mb:.2f} MB")
    df, sampled = read_for_display(path, max_rows=DEFAULT_SAMPLE_ROWS)
    summary_cols = summary.columns
    summary_dtypes = summary.dtypes
    path_stem = path.stem

if sampled:
    st.warning(f"This file is large, so the explorer loaded the first {len(df):,} rows for interactive filtering and charting. Downloads below contain the currently loaded sample.")

with st.container(horizontal=True, horizontal_alignment="distribute"):
    st.metric("Loaded rows", f"{len(df):,}", border=True)
    st.metric("Columns", len(df.columns), border=True)
    st.metric("Duplicate rows", int(df.duplicated().sum()) if not df.empty else 0, border=True)
    st.metric("Missing cells", int(df.isna().sum().sum()) if not df.empty else 0, border=True)

tabs = st.tabs(["Preview", "Schema", "Quality", "Charts", "Compare / Diff", "Download"])

with tabs[0]:
    filtered = df.copy()
    if "battery_id" in filtered.columns:
        batteries = ["All"] + safe_unique(filtered, "battery_id")
        battery = st.selectbox("Battery ID", batteries)
        if battery != "All":
            filtered = filtered[filtered["battery_id"] == battery]
    if "cycle_number" in filtered.columns:
        cycle_values = safe_unique(filtered, "cycle_number")
        if cycle_values:
            min_cycle, max_cycle = int(min(cycle_values)), int(max(cycle_values))
            selected_range = st.slider("Cycle number range", min_cycle, max_cycle, (min_cycle, max_cycle))
            filtered = filtered[(filtered["cycle_number"] >= selected_range[0]) & (filtered["cycle_number"] <= selected_range[1])]
    if "elapsed_seconds" in filtered.columns:
        elapsed = pd.to_numeric(filtered["elapsed_seconds"], errors="coerce")
        if elapsed.notna().any():
            low, high = float(elapsed.min()), float(elapsed.max())
            interval = st.slider("Elapsed seconds", low, high, (low, high))
            filtered = filtered[(elapsed >= interval[0]) & (elapsed <= interval[1])]
    selected_cols = st.multiselect("Columns", list(filtered.columns), default=list(filtered.columns[: min(8, len(filtered.columns))]))
    display_df = filtered[selected_cols] if selected_cols else filtered
    st.dataframe(display_df.head(2000), width="stretch", hide_index=True)

with tabs[1]:
    schema_df = pd.DataFrame({"Column": summary_cols, "Type": [summary_dtypes[column] for column in summary_cols]})
    st.dataframe(schema_df, width="stretch", hide_index=True)

with tabs[2]:
    st.dataframe(quality_summary(df), width="stretch", hide_index=True)
    if "battery_id" in df.columns:
        st.write(f"Unique batteries in loaded data: {df['battery_id'].nunique(dropna=True)}")
    if "cycle_number" in df.columns:
        st.write(f"Cycle range in loaded data: {df['cycle_number'].min()} to {df['cycle_number'].max()}")

with tabs[3]:
    integrity_warning("Dataset plots are descriptive summaries of recorded or processed values.")
    if "elapsed_seconds" in df.columns:
        y_options = [c for c in ["voltage_measured", "current_measured", "temperature_measured"] if c in df.columns]
        if y_options:
            st.pyplot(line_chart(df, "elapsed_seconds", y_options, "Measurements over elapsed time"), alt="Line chart of selected measured values over elapsed seconds")
    if "capacity_ah" in df.columns:
        x_col = "cycle_order" if "cycle_order" in df.columns else "cycle_number" if "cycle_number" in df.columns else "cycle_id"
        if x_col in df.columns:
            st.pyplot(line_chart(df.dropna(subset=["capacity_ah"]), x_col, ["capacity_ah"], "Capacity across cycles", "Capacity (Ah)"), alt="Line chart of capacity across available cycles")
    if "temperature_measured" in df.columns:
        st.pyplot(histogram(df, "temperature_measured", "Temperature distribution", "Temperature (C)"), alt="Histogram of measured temperature values")
    numeric = numeric_columns(df)
    if not numeric:
        st.info("No numeric columns are available for charts in the loaded sample.")

with tabs[4]:
    st.subheader("Compare with Uploaded CSV", icon=":material/difference:")
    st.markdown(
        f"Upload a CSV file below to calculate and visualize differences against **{selected_name}**."
    )
    uploaded_diff = st.file_uploader(
        "Upload CSV file to see differences",
        type=["csv"],
        key="explorer_diff_uploader",
        help="Upload a CSV file to inspect schema differences, summary statistics deltas, and cell-level changes against the selected dataset.",
    )
    if uploaded_diff is not None:
        try:
            with st.spinner("Analyzing differences..."):
                diff_df = pd.read_csv(uploaded_diff, low_memory=False)
            render_diff_view(df_base=df, df_comp=diff_df, base_name=selected_name, comp_name=uploaded_diff.name)
        except Exception as exc:
            st.error(f"Error reading uploaded CSV: {exc}")
    else:
        st.info("Upload a CSV file above to view side-by-side differences, schema deltas, and statistical shifts.")
        st.page_link("pages/8_CSV_Comparison.py", label="Open dedicated CSV Comparison page", icon=":material/open_in_new:")

with tabs[5]:
    st.download_button(
        "Download loaded records",
        data=dataframe_download(df),
        file_name=f"{path_stem}_loaded_records.csv",
        mime="text/csv",
    )
