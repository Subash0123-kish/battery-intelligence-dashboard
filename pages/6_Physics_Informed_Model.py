import streamlit as st

from utils.config import KEY_OUTPUTS, relative_to_project
from utils.data_loader import dataframe_download, read_csv
from utils.plotting import histogram, line_chart, scatter_actual_pred
from utils.ui import apply_theme, info_panel, integrity_warning, page_intro, sidebar_status


apply_theme()
sidebar_status()
page_intro("Physics-informed model", "Experimental empirical thermal and PINN artifacts.", icon=":material/neurology:")
integrity_warning("The physics and PINN results are experimental prototypes, not validated electrothermal models.")

info_panel(
    "The saved empirical relationship is treated as a simplified physics-motivated model similar to "
    "dT/dt = beta_0 + beta_1 * I^2 + beta_2 * T. Early physical parameters were placeholders and "
    "were not experimentally calibrated."
)

metrics_tabs = st.tabs(["Metrics", "Training History", "Predictions", "Assumptions"])

with metrics_tabs[0]:
    for label in ["Physics thermal metrics", "PINN thermal metrics", "Thermal common-test comparison"]:
        path = KEY_OUTPUTS[label]
        if path.exists():
            st.caption(label)
            st.dataframe(read_csv(path), width="stretch", hide_index=True)
        else:
            st.info(f"Missing: {relative_to_project(path)}")

with metrics_tabs[1]:
    history_path = KEY_OUTPUTS["PINN training history"]
    if history_path.exists():
        history = read_csv(history_path)
        st.dataframe(history, width="stretch", hide_index=True)
        loss_cols = [c for c in ["total_loss", "data_loss", "normalized_physics_loss"] if c in history.columns]
        if "epoch" in history.columns and loss_cols:
            st.pyplot(line_chart(history, "epoch", loss_cols, "PINN training history", "Loss"), alt="Line chart of PINN training losses by epoch")
    else:
        st.info("No PINN training history file is available.")

with metrics_tabs[2]:
    pred_path = KEY_OUTPUTS["Physics thermal predictions"]
    if pred_path.exists():
        pred = read_csv(pred_path)
        st.caption(relative_to_project(pred_path))
        if {"next_temperature", "predicted_next_temperature"}.issubset(pred.columns):
            st.pyplot(scatter_actual_pred(pred, "next_temperature", "predicted_next_temperature", "Physics empirical prediction"), alt="Scatter plot comparing observed and physics empirical predicted next temperature")
            tmp = pred.copy()
            tmp["residual"] = tmp["next_temperature"] - tmp["predicted_next_temperature"]
            st.pyplot(histogram(tmp, "residual", "Physics empirical residual distribution", "Temperature error (C)"), alt="Histogram of physics empirical model residuals")
        st.dataframe(pred.head(1000), width="stretch", hide_index=True)
        st.download_button("Download physics predictions", dataframe_download(pred), "physics_thermal_predictions_dashboard.csv", "text/csv")
    else:
        st.info("Prediction visualization requires outputs/physics_thermal_predictions.csv or a compatible prediction file.")

with metrics_tabs[3]:
    st.markdown(
        """
        - The thermal target is the next recorded temperature observation.
        - Observation intervals may vary across cycles and batteries.
        - The empirical model is not a complete electrothermal representation.
        - PINN metrics should be compared only against artifacts evaluated on compatible data.
        - Predictive accuracy alone does not establish battery safety, field readiness, or causal validity.
        """
    )

