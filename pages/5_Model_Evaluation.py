import pandas as pd
import streamlit as st

from utils.config import KEY_OUTPUTS, OUTPUT_DIR, REPORT_DIR, relative_to_project
from utils.data_loader import dataframe_download, read_csv
from utils.metrics import metrics_frame
from utils.plotting import bar_chart, histogram, residual_plot, scatter_actual_pred
from utils.ui import apply_theme, integrity_warning, page_intro, sidebar_status


apply_theme()
sidebar_status()
page_intro("Model evaluation", "Comparison of saved model metrics, predictions, residuals, and battery-level errors.", icon=":material/analytics:")
integrity_warning("Metrics are grouped by saved artifact. Common-test-set results are preferred when available.")

metric_sources = {
    "Thermal common test": KEY_OUTPUTS["Thermal common-test comparison"],
    "Thermal final rankings": KEY_OUTPUTS["Thermal final rankings"],
    "RUL": KEY_OUTPUTS["RUL model comparison"],
    "SOH": KEY_OUTPUTS["SOH report comparison"],
    "Physics empirical": KEY_OUTPUTS["Physics thermal metrics"],
    "PINN": KEY_OUTPUTS["PINN thermal metrics"],
}

frames = []
for domain, path in metric_sources.items():
    if path.exists():
        frame = read_csv(path).copy()
        frame.insert(0, "Artifact", domain)
        frame.insert(1, "Path", relative_to_project(path))
        frames.append(frame)

if frames:
    metrics = pd.concat(frames, ignore_index=True, sort=False)
    st.subheader("Model Comparison Table")
    st.dataframe(metrics, width="stretch", hide_index=True)
    st.download_button("Download model comparison table", dataframe_download(metrics), "model_comparison_dashboard.csv", "text/csv")

    metric_col_options = [c for c in metrics.columns if c.upper() in {"MAE", "MAE_C", "RMSE", "RMSE_C", "R2"} or "MAE" in c.upper() or "RMSE" in c.upper()]
    if "Model" in metrics.columns and metric_col_options:
        selected_metric = st.selectbox("Metric chart", metric_col_options)
        chart_df = metrics.dropna(subset=["Model", selected_metric]).copy()
        chart_df["Model label"] = chart_df["Artifact"].astype(str) + ": " + chart_df["Model"].astype(str)
        st.pyplot(bar_chart(chart_df, "Model label", selected_metric, f"{selected_metric} comparison", selected_metric), alt="Bar chart comparing selected model metric")
else:
    st.info("No saved metric comparison files were found.")

st.subheader("Prediction Error Analysis")
prediction_options = {
    "Thermal common-test predictions": KEY_OUTPUTS["Thermal common-test predictions"],
    "Thermal evaluated predictions": KEY_OUTPUTS["Thermal evaluated predictions"],
    "RUL evaluated predictions": KEY_OUTPUTS["RUL evaluated predictions"],
    "SOH test predictions": KEY_OUTPUTS["SOH report predictions"],
    "Physics thermal predictions": KEY_OUTPUTS["Physics thermal predictions"],
}
available = {name: path for name, path in prediction_options.items() if path.exists()}
if not available:
    st.info("No prediction files are available for residual analysis.")
else:
    selected = st.selectbox("Prediction artifact", list(available.keys()))
    pred = read_csv(available[selected])
    st.caption(relative_to_project(available[selected]))
    st.dataframe(pred.head(1000), width="stretch", hide_index=True)

    if "Thermal common" in selected:
        actual = "actual_next_temperature"
        preds = {"Persistence Baseline": "predicted_baseline", "Linear Regression": "predicted_lr", "Random Forest": "predicted_rf"}
    elif "Thermal evaluated" in selected:
        actual = "actual_next_temperature"
        preds = {"Linear Regression": "predicted_next_lr", "Random Forest": "predicted_next_rf"}
    elif "RUL" in selected:
        actual = "actual_rul"
        preds = {"Linear Regression": "predicted_rul_lr", "Random Forest": "predicted_rul_rf"}
    elif "SOH" in selected:
        actual = "actual_soh"
        preds = {"Linear Regression": "predicted_lr", "Random Forest Baseline": "predicted_rf_baseline", "Random Forest Multi": "predicted_rf_multi"}
    else:
        actual = "next_temperature"
        preds = {"Physics empirical": "predicted_next_temperature"}

    preds = {name: col for name, col in preds.items() if actual in pred.columns and col in pred.columns}
    if preds:
        computed_metrics = metrics_frame(pred, actual, preds)
        st.dataframe(computed_metrics, width="stretch", hide_index=True)
        model = st.selectbox("Model", list(preds.keys()))
        pred_col = preds[model]
        residual_frame = pred.copy()
        residual_frame["dashboard_residual"] = residual_frame[actual] - residual_frame[pred_col]
        residual_frame["dashboard_abs_error"] = residual_frame["dashboard_residual"].abs()
        st.pyplot(scatter_actual_pred(residual_frame, actual, pred_col, f"Actual versus predicted: {model}"), alt="Scatter plot comparing actual values with selected model predictions")
        st.pyplot(residual_plot(residual_frame, pred_col, "dashboard_residual", f"Residuals: {model}"), alt="Residual scatter plot for selected model")
        st.pyplot(histogram(residual_frame, "dashboard_residual", f"Residual distribution: {model}"), alt="Histogram of selected model residuals")
        st.subheader("Largest Absolute Errors")
        st.dataframe(residual_frame.sort_values("dashboard_abs_error", ascending=False).head(50), width="stretch", hide_index=True)
        st.download_button("Download prediction errors", dataframe_download(residual_frame), "prediction_errors_dashboard.csv", "text/csv")
    else:
        st.info("This artifact does not contain a recognized actual/predicted column pair.")

st.subheader("Battery-Level Evaluation")
for path in [OUTPUT_DIR / "final_thermal_battery_metrics.csv", OUTPUT_DIR / "rul_battery_error_summary.csv", REPORT_DIR / "soh_battery_error_analysis.csv"]:
    if path.exists():
        st.caption(relative_to_project(path))
        st.dataframe(read_csv(path), width="stretch", hide_index=True)

