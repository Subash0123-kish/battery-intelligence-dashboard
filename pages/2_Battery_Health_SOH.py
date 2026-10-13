import pandas as pd
import streamlit as st

from utils.config import KEY_OUTPUTS, PROCESSED_DATASETS, relative_to_project
from utils.data_loader import dataframe_download, quality_summary, read_csv, safe_unique
from utils.plotting import bar_chart, line_chart, scatter_actual_pred
from utils.ui import apply_theme, integrity_warning, page_intro, sidebar_status


apply_theme()
sidebar_status()
page_intro("Battery health (SOH)", "State-of-health analysis from saved validated SOH and SOH report outputs.", icon=":material/battery_charging_full:")
integrity_warning("SOH values are displayed as saved. Values above 100 percent are not clipped or removed.")

soh_path = PROCESSED_DATASETS["SOH validated"]
if not soh_path.exists():
    st.error(f"SOH data is unavailable. Expected file: {relative_to_project(soh_path)}")
    st.stop()

soh = read_csv(soh_path)
st.caption(relative_to_project(soh_path))

batteries = safe_unique(soh, "battery_id")
selected_battery = st.selectbox("Battery", batteries) if batteries else None
battery_df = soh[soh["battery_id"] == selected_battery].copy() if selected_battery else soh.copy()

with st.container(horizontal=True, horizontal_alignment="distribute"):
    st.metric("Rows", f"{len(battery_df):,}", border=True)
    st.metric("Min SOH", f"{battery_df['SOH_percent'].min():.2f}%" if "SOH_percent" in battery_df.columns else "Unavailable", border=True)
    st.metric("Max SOH", f"{battery_df['SOH_percent'].max():.2f}%" if "SOH_percent" in battery_df.columns else "Unavailable", border=True)
    st.metric("Capacity rows", int(battery_df["capacity_ah"].notna().sum()) if "capacity_ah" in battery_df.columns else "Unavailable", border=True)

if "SOH_percent" in soh.columns and (soh["SOH_percent"] > 100).any():
    st.warning("The saved SOH data includes values above 100 percent. They are retained because the reference capacity and cycle mapping require validation.")

x_col = "cycle_order" if "cycle_order" in battery_df.columns else "cycle_number" if "cycle_number" in battery_df.columns else "cycle_id"
if x_col in battery_df.columns and "SOH_percent" in battery_df.columns:
    st.pyplot(line_chart(battery_df, x_col, ["SOH_percent"], "SOH over recorded cycle order", "SOH (%)"), alt="Line chart of SOH percentage across recorded cycle order")
if x_col in battery_df.columns and "capacity_ah" in battery_df.columns:
    y_cols = ["capacity_ah"]
    if "reference_capacity_ah" in battery_df.columns:
        y_cols.append("reference_capacity_ah")
    st.pyplot(line_chart(battery_df, x_col, y_cols, "Capacity and reference capacity", "Capacity (Ah)"), alt="Line chart of capacity and available reference capacity")

st.subheader("Battery Comparison")
if {"battery_id", "SOH_percent"}.issubset(soh.columns):
    comparison = soh.groupby("battery_id", as_index=False).agg(
        observations=("SOH_percent", "count"),
        min_soh=("SOH_percent", "min"),
        mean_soh=("SOH_percent", "mean"),
        max_soh=("SOH_percent", "max"),
    )
    st.dataframe(comparison, width="stretch", hide_index=True)
    st.pyplot(bar_chart(comparison, "battery_id", "min_soh", "Minimum SOH by battery", "SOH (%)"), alt="Bar chart of minimum SOH by battery")

with st.expander("SOH data quality"):
    st.dataframe(quality_summary(soh), width="stretch", hide_index=True)

pred_path = KEY_OUTPUTS["SOH report predictions"]
if pred_path.exists():
    st.subheader("Saved SOH Model Predictions")
    pred = read_csv(pred_path)
    st.dataframe(pred.head(1000), width="stretch", hide_index=True)
    prediction_cols = [c for c in pred.columns if c.startswith("predicted")]
    if "actual_soh" in pred.columns and prediction_cols:
        selected_prediction = st.selectbox("Prediction column", prediction_cols)
        st.pyplot(scatter_actual_pred(pred, "actual_soh", selected_prediction, "Actual versus predicted SOH"), alt="Scatter plot comparing actual SOH to selected prediction")
    comparison_path = KEY_OUTPUTS["SOH report comparison"]
    if comparison_path.exists():
        st.dataframe(read_csv(comparison_path), width="stretch", hide_index=True)

st.download_button("Download SOH records", dataframe_download(battery_df), "soh_filtered_records.csv", "text/csv")

