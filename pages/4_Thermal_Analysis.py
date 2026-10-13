import streamlit as st

from utils.config import KEY_OUTPUTS, PROCESSED_DATASETS, SOURCE_DATASETS, relative_to_project
from utils.data_loader import dataframe_download, read_csv, read_for_display, safe_unique
from utils.plotting import histogram, line_chart, residual_plot, scatter_actual_pred
from utils.ui import apply_theme, integrity_warning, page_intro, sidebar_status


apply_theme()
sidebar_status()
page_intro("Thermal analysis", "Measured discharge temperature/current/voltage and saved next-observation thermal predictions.", icon=":material/device_thermostat:")
integrity_warning("Thermal targets represent the next recorded observation unless the data construction proves another horizon.")

discharge_path = SOURCE_DATASETS["Discharge dataset"]
thermal_path = PROCESSED_DATASETS["Thermal prediction dataset"]
prediction_path = KEY_OUTPUTS["Thermal common-test predictions"]

tabs = st.tabs(["Measured Discharge", "Thermal Prediction Dataset", "Saved Predictions"])

with tabs[0]:
    if not discharge_path.exists():
        st.error(f"Missing discharge file: {relative_to_project(discharge_path)}")
    else:
        discharge, sampled = read_for_display(discharge_path)
        if sampled:
            st.warning("The discharge file is large, so this view uses a loaded sample.")
        batteries = safe_unique(discharge, "battery_id")
        battery = st.selectbox("Battery", batteries, key="measured_battery") if batteries else None
        view = discharge[discharge["battery_id"] == battery] if battery else discharge
        cycles = safe_unique(view, "cycle_number", limit=500)
        cycle = st.selectbox("Cycle", cycles, key="measured_cycle") if cycles else None
        if cycle is not None:
            view = view[view["cycle_number"] == cycle]
        if "elapsed_seconds" in view.columns:
            y_cols = [c for c in ["temperature_measured", "current_measured", "voltage_measured"] if c in view.columns]
            st.pyplot(line_chart(view, "elapsed_seconds", y_cols, "Recorded discharge measurements"), alt="Line chart of recorded discharge measurements over elapsed seconds")
        if "temperature_measured" in view.columns:
            st.pyplot(histogram(view, "temperature_measured", "Temperature distribution", "Temperature (C)"), alt="Histogram of measured temperature values")
        st.dataframe(view.head(1000), width="stretch", hide_index=True)
        st.download_button("Download filtered discharge records", dataframe_download(view), "thermal_discharge_filtered.csv", "text/csv")

with tabs[1]:
    if not thermal_path.exists():
        st.info(f"Thermal prediction dataset is not available: {relative_to_project(thermal_path)}")
    else:
        thermal, sampled = read_for_display(thermal_path)
        if sampled:
            st.warning("The thermal prediction dataset is large, so this tab uses a loaded sample.")
        st.dataframe(thermal.head(1000), width="stretch", hide_index=True)
        if {"temperature_measured", "next_temperature"}.issubset(thermal.columns):
            st.pyplot(scatter_actual_pred(thermal, "temperature_measured", "next_temperature", "Current temperature versus next recorded temperature"), alt="Scatter plot of current temperature against next recorded temperature")
        if "time_to_next_seconds" in thermal.columns:
            st.pyplot(histogram(thermal, "time_to_next_seconds", "Observation interval distribution", "Seconds"), alt="Histogram of observation intervals in seconds")

with tabs[2]:
    if not prediction_path.exists():
        st.info(f"Saved thermal predictions are not available: {relative_to_project(prediction_path)}")
    else:
        pred = read_csv(prediction_path)
        batteries = safe_unique(pred, "battery_id")
        battery = st.selectbox("Battery", batteries, key="pred_battery") if batteries else None
        pred_view = pred[pred["battery_id"] == battery] if battery else pred
        pred_cols = [c for c in ["predicted_baseline", "predicted_lr", "predicted_rf"] if c in pred_view.columns]
        if "elapsed_seconds" in pred_view.columns:
            y_cols = [c for c in ["actual_next_temperature", *pred_cols] if c in pred_view.columns]
            st.pyplot(line_chart(pred_view, "elapsed_seconds", y_cols, "Actual versus predicted next temperature", "Temperature (C)"), alt="Line chart comparing actual and predicted next temperature")
        if "actual_next_temperature" in pred_view.columns and pred_cols:
            selected_pred = st.selectbox("Prediction column", pred_cols)
            st.pyplot(scatter_actual_pred(pred_view, "actual_next_temperature", selected_pred, "Actual versus predicted next temperature"), alt="Scatter plot comparing actual next temperature and selected prediction")
            tmp = pred_view.copy()
            tmp["residual"] = tmp["actual_next_temperature"] - tmp[selected_pred]
            st.pyplot(residual_plot(tmp, selected_pred, "residual", "Prediction residuals"), alt="Residual scatter plot for selected thermal prediction")
            st.pyplot(histogram(tmp, "residual", "Prediction error distribution", "Temperature error (C)"), alt="Histogram of thermal prediction errors")
        st.download_button("Download filtered thermal predictions", dataframe_download(pred_view), "thermal_predictions_filtered.csv", "text/csv")

