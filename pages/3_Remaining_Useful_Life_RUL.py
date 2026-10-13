import streamlit as st

from utils.config import KEY_OUTPUTS, PROCESSED_DATASETS, OUTPUT_DIR, relative_to_project
from utils.data_loader import dataframe_download, read_csv, safe_unique
from utils.metrics import metrics_frame
from utils.plotting import bar_chart, histogram, line_chart, residual_plot, scatter_actual_pred
from utils.ui import apply_theme, integrity_warning, page_intro, sidebar_status


apply_theme()
sidebar_status()
page_intro("Remaining useful life (RUL)", "Saved cycle-level RUL targets, predictions, and error summaries.", icon=":material/timeline:")
integrity_warning("RUL interpretation depends on the cycles_left target provenance, end-of-life definition, and cycle numbering.")

feature_path = PROCESSED_DATASETS["RUL cycle features"]
prediction_path = KEY_OUTPUTS["RUL evaluated predictions"]
comparison_path = KEY_OUTPUTS["RUL model comparison"]

if not feature_path.exists() and not prediction_path.exists():
    st.error("No RUL feature or prediction files are available.")
    st.stop()

features = read_csv(feature_path) if feature_path.exists() else None
predictions = read_csv(prediction_path) if prediction_path.exists() else None

source_df = predictions if predictions is not None else features
batteries = safe_unique(source_df, "battery_id")
selected_battery = st.selectbox("Battery", batteries) if batteries else None

if features is not None:
    feature_view = features[features["battery_id"] == selected_battery] if selected_battery and "battery_id" in features.columns else features
    st.subheader("Recorded RUL Target")
    if {"cycle_number", "cycles_left"}.issubset(feature_view.columns):
        st.pyplot(line_chart(feature_view, "cycle_number", ["cycles_left"], "Cycles left target by cycle", "Cycles"), alt="Line chart of cycles left target by cycle number")
    st.dataframe(feature_view.head(1000), width="stretch", hide_index=True)

if predictions is not None:
    st.subheader("Saved RUL Predictions")
    pred_view = predictions[predictions["battery_id"] == selected_battery] if selected_battery and "battery_id" in predictions.columns else predictions
    y_cols = [c for c in ["actual_rul", "predicted_rul_lr", "predicted_rul_rf"] if c in pred_view.columns]
    if "cycle_number" in pred_view.columns and y_cols:
        st.pyplot(line_chart(pred_view, "cycle_number", y_cols, "Actual and predicted RUL", "Cycles"), alt="Line chart comparing actual and predicted RUL over cycles")
    pred_cols = {"Linear Regression": "predicted_rul_lr", "Random Forest": "predicted_rul_rf"}
    available_pred_cols = {k: v for k, v in pred_cols.items() if v in pred_view.columns}
    if "actual_rul" in pred_view.columns and available_pred_cols:
        computed = metrics_frame(pred_view, "actual_rul", available_pred_cols)
        st.dataframe(computed, width="stretch", hide_index=True)
        selected_model = st.selectbox("Prediction model", list(available_pred_cols.keys()))
        pred_col = available_pred_cols[selected_model]
        residual_col = "residual_lr" if pred_col.endswith("_lr") else "residual_rf"
        st.pyplot(scatter_actual_pred(pred_view, "actual_rul", pred_col, f"Actual versus predicted RUL: {selected_model}"), alt="Scatter plot comparing actual and predicted RUL")
        if residual_col in pred_view.columns:
            st.pyplot(residual_plot(pred_view, pred_col, residual_col, f"Residuals: {selected_model}"), alt="Residual scatter plot for selected RUL model")
            st.pyplot(histogram(pred_view, residual_col, f"Residual distribution: {selected_model}", "Residual (cycles)"), alt="Histogram of RUL residuals")
    st.download_button("Download filtered RUL predictions", dataframe_download(pred_view), "rul_filtered_predictions.csv", "text/csv")

if comparison_path.exists():
    st.subheader("Saved Model Comparison")
    comparison = read_csv(comparison_path)
    st.dataframe(comparison, width="stretch", hide_index=True)
    mae_col = next((c for c in comparison.columns if "MAE" in c.upper()), None)
    if mae_col and "Model" in comparison.columns:
        st.pyplot(bar_chart(comparison, "Model", mae_col, "RUL MAE comparison", mae_col), alt="Bar chart comparing RUL MAE by model")

battery_summary_path = OUTPUT_DIR / "rul_battery_error_summary.csv"
if battery_summary_path.exists():
    st.subheader("Per-Battery Error Summary")
    st.dataframe(read_csv(battery_summary_path), width="stretch", hide_index=True)

