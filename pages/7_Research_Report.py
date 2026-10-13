from pathlib import Path

import streamlit as st

from utils.config import OUTPUT_DIR, REPORT_FILES, relative_to_project
from utils.ui import apply_theme, integrity_warning, page_intro, sidebar_status


apply_theme()
sidebar_status()
page_intro("Research report", "Saved project documentation, summaries, and scientific limitations.", icon=":material/article:")
integrity_warning("This report page displays existing written artifacts and does not invent missing conclusions.")

available_reports = {name: path for name, path in REPORT_FILES.items() if path.exists()}
thermal_summary = OUTPUT_DIR / "thermal_research_summary.txt"
if thermal_summary.exists() and "Thermal research summary" not in available_reports:
    available_reports["Thermal research summary"] = thermal_summary

if available_reports:
    selected = st.selectbox("Report", list(available_reports.keys()))
    path = available_reports[selected]
    text = path.read_text(encoding="utf-8", errors="replace")
    st.caption(relative_to_project(path))
    if path.suffix.lower() == ".md":
        st.markdown(text)
    else:
        st.text_area("Report content", text, height=520)
    st.download_button("Download report", data=text.encode("utf-8"), file_name=path.name, mime="text/plain")
else:
    st.info("No saved report files were found in outputs/. Expected examples include scientific_validation_report.txt or battery_research_report.md.")

st.subheader("Documentation Coverage")
st.markdown(
    """
    The dashboard pages expose objectives, dataset availability, preprocessing artifacts, SOH,
    RUL, thermal prediction, model evaluation, physics-informed experiments, limitations, and
    downloadable results where the corresponding files exist.
    """
)

st.subheader("Core Scientific Limitations")
st.markdown(
    """
    - SOH reference capacity and chronological cycle mapping require verification.
    - Numeric cycle_id is not automatically treated as cycle_number.
    - cycles_left provenance must be verified before making RUL claims.
    - Thermal prediction targets the next recorded observation, not a fixed future horizon.
    - Train/test battery separation must be verified in the original training workflow.
    - Early thermal parameters were not experimentally calibrated.
    - The PINN is experimental and not a validated electrothermal model.
    - Predictive accuracy does not establish battery safety or deployment readiness.
    """
)

