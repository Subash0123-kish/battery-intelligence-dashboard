from pathlib import Path

import pandas as pd
import streamlit as st

from utils.config import HERO_IMAGE, KEY_OUTPUTS, PROCESSED_DATASETS, SOURCE_DATASETS, relative_to_project
from utils.data_loader import build_availability_table, count_csv_rows, quality_summary, read_csv, summarize_csv
from utils.ui import apply_theme, info_panel, integrity_warning, page_card, sidebar_status


apply_theme()
sidebar_status()

hero_left, hero_right = st.columns([0.98, 1.02], vertical_alignment="center")
with hero_left:
    st.markdown(
        """
        <div class="hero-copy">
            <div class="hero-kicker">NASA lithium-ion battery aging dataset</div>
            <div class="hero-title">Battery Intelligence</div>
            <div class="hero-subtitle">
                Interactive research dashboard for battery degradation, SOH, RUL,
                thermal prediction, and physics-informed model artifacts saved in this workspace.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(":blue-badge[Dataset explorer] :purple-badge[CSV diff & comparison] :green-badge[Model evaluation] :orange-badge[Scientific limitations visible]")
    with st.container(horizontal=True):
        st.page_link("pages/1_Dataset_Explorer.py", label="Explore data", icon=":material/database:")
        st.page_link("pages/8_CSV_Comparison.py", label="Compare CSVs", icon=":material/difference:")
        st.page_link("pages/5_Model_Evaluation.py", label="Review models", icon=":material/analytics:")
        st.page_link("pages/7_Research_Report.py", label="Read report", icon=":material/article:")
with hero_right:
    if HERO_IMAGE.exists():
        st.image(str(HERO_IMAGE), alt="Laboratory battery cells with thermal heatmap visualization for the Battery Intelligence dashboard", width="stretch")
    else:
        st.info("Hero image is unavailable. The dashboard remains fully functional.")


def safe_row_count(path: Path) -> int | None:
    return count_csv_rows(str(path.resolve())) if path.exists() else None


source_rows = {name: safe_row_count(path) for name, path in SOURCE_DATASETS.items()}
discharge_path = SOURCE_DATASETS["Discharge dataset"]
meta_path = SOURCE_DATASETS["Metadata dataset"]
thermal_obs = PROCESSED_DATASETS["Physics thermal observations"]

battery_count = None
if meta_path.exists():
    try:
        battery_count = int(read_csv(meta_path, usecols=["battery_id"])["battery_id"].nunique())
    except Exception:
        battery_count = None

processed_thermal_rows = safe_row_count(thermal_obs)
model_result_files = sum(path.exists() for path in KEY_OUTPUTS.values())

st.space("small")
with st.container(horizontal=True, horizontal_alignment="distribute"):
    st.metric("Batteries", battery_count if battery_count is not None else "Unavailable", border=True)
    st.metric("Discharge records", f"{source_rows.get('Discharge dataset'):,}" if source_rows.get("Discharge dataset") is not None else "Unavailable", border=True)
    st.metric("Charge records", f"{source_rows.get('Charge dataset'):,}" if source_rows.get("Charge dataset") is not None else "6,512,876 (Catalog)", border=True)
    st.metric("Impedance records", f"{source_rows.get('Impedance dataset'):,}" if source_rows.get("Impedance dataset") is not None else "Unavailable", border=True)
    st.metric("Thermal observations", f"{processed_thermal_rows:,}" if processed_thermal_rows is not None else "770,070 (Catalog)", border=True)
    st.metric("Model result files", model_result_files, border=True)

st.space("medium")

left, right = st.columns([1.05, 0.95])
with left:
    with st.container(border=True, height="stretch"):
        st.subheader("Research workflow", icon=":material/experiment:")
        info_panel(
            "The application focuses on health estimation, RUL analysis, next-observation thermal "
            "prediction, and experimental physics-informed modeling. It reuses saved datasets and "
            "model outputs; it does not retrain models while the dashboard opens."
        )
        st.write(
            """
            Inspect source and processed data, compare saved model metrics, review residuals and
            battery-level behavior, and download filtered records for offline analysis.
            """
        )

with right:
    with st.container(border=True, height="stretch"):
        st.subheader("Research limitations", icon=":material/warning:")
        integrity_warning("The overview highlights unresolved validation issues across the project.")

st.subheader("Dataset availability", icon=":material/folder_open:")
availability = pd.concat(
    [
        build_availability_table(SOURCE_DATASETS, include_rows=True).assign(Group="Source"),
        build_availability_table(PROCESSED_DATASETS, include_rows=False).assign(Group="Processed"),
        build_availability_table(KEY_OUTPUTS, include_rows=False).assign(Group="Outputs"),
    ],
    ignore_index=True,
)
filter_left, filter_mid, filter_right = st.columns([1.1, 0.75, 1.15], vertical_alignment="bottom")
with filter_left:
    group_filter = st.segmented_control("Artifact group", ["All", "Source", "Processed", "Outputs"], default="All")
with filter_mid:
    available_only = st.toggle("Available only", value=False)
with filter_right:
    search_term = st.text_input("Search datasets and outputs", placeholder="SOH, thermal, RUL...")

availability_view = availability.copy()
if group_filter != "All":
    availability_view = availability_view[availability_view["Group"] == group_filter]
if available_only:
    availability_view = availability_view[availability_view["Available"]]
if search_term:
    mask = availability_view[["Dataset", "Path", "Group"]].astype(str).apply(lambda col: col.str.contains(search_term, case=False, na=False))
    availability_view = availability_view[mask.any(axis=1)]
st.dataframe(availability_view, width="stretch", hide_index=True)

st.subheader("Data quality summary", icon=":material/fact_check:")
quality_records = []
for name, path in {**SOURCE_DATASETS, **PROCESSED_DATASETS}.items():
    summary = summarize_csv(path)
    quality_records.append(
        {
            "Dataset": name,
            "Path": relative_to_project(path),
            "Available": summary.exists,
            "Columns": len(summary.columns),
            "Size MB": round(summary.size_mb, 2),
            "Schema issue": summary.error,
        }
    )
quality_df = pd.DataFrame(quality_records)
st.dataframe(quality_df, width="stretch", hide_index=True)

if meta_path.exists():
    with st.expander("Metadata missing values and duplicate records", expanded=False, icon=":material/table_chart:"):
        meta_sample = read_csv(meta_path)
        st.write(f"Duplicate rows: {int(meta_sample.duplicated().sum())}")
        st.dataframe(quality_summary(meta_sample), width="stretch", hide_index=True)

st.subheader("Recent research results", icon=":material/query_stats:")
result_family = st.segmented_control("Result family", ["Thermal", "RUL", "SOH", "Physics/PINN"], default="Thermal")
if result_family == "Thermal":
    for label in ("Thermal common-test comparison", "Thermal final rankings"):
        path = KEY_OUTPUTS[label]
        if path.exists():
            st.caption(label)
            st.dataframe(read_csv(path), width="stretch", hide_index=True)
elif result_family == "RUL":
    path = KEY_OUTPUTS["RUL model comparison"]
    if path.exists():
        st.dataframe(read_csv(path), width="stretch", hide_index=True)
    else:
        st.info("RUL comparison output is not available.")
elif result_family == "SOH":
    path = KEY_OUTPUTS["SOH report comparison"]
    if path.exists():
        st.dataframe(read_csv(path), width="stretch", hide_index=True)
    else:
        st.info("SOH report comparison output is not available.")
else:
    for label in ("Physics thermal metrics", "PINN thermal metrics"):
        path = KEY_OUTPUTS[label]
        if path.exists():
            st.caption(label)
            st.dataframe(read_csv(path), width="stretch", hide_index=True)

st.subheader("Quick navigation", icon=":material/near_me:")
nav_cols = st.columns(4)
with nav_cols[0]:
    page_card("Dataset explorer", "Filter records, inspect schemas, and download loaded samples.", "pages/1_Dataset_Explorer.py", ":material/database:")
with nav_cols[1]:
    page_card("Battery health", "Review SOH records and capacity behavior by battery.", "pages/2_Battery_Health_SOH.py", ":material/battery_charging_full:")
with nav_cols[2]:
    page_card("RUL analysis", "Compare recorded targets with saved RUL predictions.", "pages/3_Remaining_Useful_Life_RUL.py", ":material/timeline:")
with nav_cols[3]:
    page_card("Thermal models", "Inspect temperature traces, residuals, and model outputs.", "pages/4_Thermal_Analysis.py", ":material/device_thermostat:")

nav_cols = st.columns(4)
with nav_cols[0]:
    page_card("Model evaluation", "Compare saved metrics and largest prediction errors.", "pages/5_Model_Evaluation.py", ":material/analytics:")
with nav_cols[1]:
    page_card("Physics-informed model", "Review empirical physics and PINN experiment artifacts.", "pages/6_Physics_Informed_Model.py", ":material/neurology:")
with nav_cols[2]:
    page_card("Research report", "Read available reports and export documentation.", "pages/7_Research_Report.py", ":material/article:")
with nav_cols[3]:
    page_card("CSV comparison", "Upload CSV files and inspect schema, statistical, and cell differences.", "pages/8_CSV_Comparison.py", ":material/difference:")

