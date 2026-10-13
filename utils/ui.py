from __future__ import annotations

import streamlit as st

from .config import APP_ICON, KEY_OUTPUTS, PROCESSED_DATASETS, PROJECT_DIR, SOURCE_DATASETS


def apply_theme() -> None:
    st.set_page_config(
        page_title="Battery Intelligence",
        page_icon=str(APP_ICON) if APP_ICON.exists() else ":material/battery_charging_full:",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    if APP_ICON.exists():
        st.logo(str(APP_ICON), size="large")
    st.markdown(
        """
        <style>
        :root {
            --navy: #172554;
            --ink: #1e293b;
            --muted: #64748b;
            --accent: #0f766e;
            --border: #dbe3ee;
            --panel: #f8fafc;
        }
        .stApp { background: #f8fafc; color: var(--ink); }
        h1, h2, h3 { color: var(--navy); letter-spacing: 0; }
        p, li, label, span { letter-spacing: 0; }
        div[data-testid="stMetric"] {
            background: white;
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 14px 16px;
            box-shadow: 0 6px 18px rgba(15, 23, 42, 0.05);
        }
        div[data-testid="stMetric"] label,
        div[data-testid="stMetric"] [data-testid="stMetricLabel"] {
            color: #475569;
        }
        div[data-testid="stMetricValue"] {
            color: #0f172a;
            font-weight: 750;
        }
        div[data-testid="stDataFrame"] {
            border: 1px solid var(--border);
            border-radius: 8px;
            overflow: hidden;
        }
        .hero-copy {
            padding: 22px 4px 10px 0;
        }
        .hero-kicker {
            color: #0f766e;
            font-size: 0.86rem;
            font-weight: 700;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            margin-bottom: 8px;
        }
        .hero-title {
            color: #0f172a;
            font-size: clamp(2.1rem, 4vw, 4.6rem);
            font-weight: 800;
            line-height: 0.98;
            margin-bottom: 14px;
        }
        .hero-subtitle {
            color: #475569;
            font-size: 1.05rem;
            max-width: 760px;
            line-height: 1.65;
        }
        .hero-image img {
            border-radius: 12px;
            box-shadow: 0 24px 60px rgba(15, 23, 42, 0.18);
            border: 1px solid #dbe3ee;
        }
        .nav-card {
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 14px;
            background: white;
            min-height: 132px;
        }
        .nav-card-title {
            color: #0f172a;
            font-weight: 750;
            margin-bottom: 4px;
        }
        .nav-card-caption {
            color: #64748b;
            font-size: 0.9rem;
            line-height: 1.45;
        }
        .section-note {
            background: #eef6f6;
            border: 1px solid #b7dddd;
            color: #134e4a;
            border-radius: 8px;
            padding: 12px 14px;
            margin: 8px 0 16px 0;
        }
        .warning-note {
            background: #fff7ed;
            border: 1px solid #fed7aa;
            color: #7c2d12;
            border-radius: 8px;
            padding: 12px 14px;
            margin: 8px 0 16px 0;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def sidebar_status() -> None:
    with st.sidebar:
        st.markdown("### Battery Intelligence")
        st.caption("Physics-Informed Battery Health & Thermal Management")
        st.markdown(":blue-badge[NASA dataset] :green-badge[Research app]")
        st.caption("Project directory")
        st.code(str(PROJECT_DIR), language=None)
        source_available = sum(path.exists() for path in SOURCE_DATASETS.values())
        processed_available = sum(path.exists() for path in PROCESSED_DATASETS.values())
        outputs_available = sum(path.exists() for path in KEY_OUTPUTS.values())
        st.metric("Source files", f"{source_available}/{len(SOURCE_DATASETS)}", border=True)
        st.metric("Processed files", f"{processed_available}/{len(PROCESSED_DATASETS)}", border=True)
        st.metric("Result files", f"{outputs_available}/{len(KEY_OUTPUTS)}", border=True)
        st.caption("Navigation is in the page list above.")


def page_intro(title: str, caption: str | None = None, icon: str | None = None) -> None:
    st.title(title, icon=icon)
    if caption:
        st.caption(caption)


def integrity_warning(context: str = "This page") -> None:
    st.markdown(
        f"""
        <div class="warning-note">
        <strong>Scientific interpretation note.</strong> {context} uses saved research artifacts only.
        SOH reference capacity, cycle mapping, RUL target provenance, train/test battery separation,
        thermal forecast horizon, and experimental physics/PINN assumptions should be verified before
        making deployment or safety claims.
        </div>
        """,
        unsafe_allow_html=True,
    )


def info_panel(text: str) -> None:
    st.markdown(f"<div class='section-note'>{text}</div>", unsafe_allow_html=True)


def page_card(title: str, caption: str, page: str, icon: str) -> None:
    with st.container(border=True, height="stretch"):
        st.markdown(f"**{title}**")
        st.caption(caption)
        st.page_link(page, label="Open page", icon=icon, width="content")
