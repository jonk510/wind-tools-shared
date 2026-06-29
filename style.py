"""
Shared Streamlit theme — dark terminal green (based on solar_pv_tool).

Usage in any tool:
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
    from shared.style import apply_theme, page_header, kpi_card

    apply_theme()
    page_header("TOOL TITLE", "subtitle line here")

    # KPI cards (put inside st.columns):
    st.markdown(kpi_card("4.2 GWh", "MWh/yr", "Annual Energy"), unsafe_allow_html=True)
"""

import streamlit as st

# ── Colour palette ────────────────────────────────────────────────────────────
_GREEN       = "#39D353"   # primary accent
_GREEN_LIGHT = "#4ADE80"   # hover / lighter accent
_GREEN_DIM   = "#86EFAC"   # secondary text
_GREEN_MUTED = "#6EE7B7"   # unit text
_BG_DARK     = "#0D1117"   # page / main background
_BG_SIDEBAR  = "#0D1A0D"   # sidebar background
_BG_CARD     = "#0D1A0D"   # KPI card background
_BORDER      = "#1A3A1A"   # card / sidebar border
_TEXT_MAIN   = "#E6EDF3"   # primary body text
_TEXT_MUTED  = "#8B949E"   # captions / muted text
_FONT        = '"Courier New", Courier, monospace'

_CSS = f"""
<style>
/* ── Global ──────────────────────────────────────────────────────────────── */
html, body, [class*="css"] {{
    font-family: {_FONT} !important;
    -webkit-font-smoothing: antialiased;
}}
.main .block-container {{
    padding-top: 1.8rem;
    padding-bottom: 4rem;
    max-width: 1400px;
}}

/* ── Sidebar ─────────────────────────────────────────────────────────────── */
section[data-testid="stSidebar"] {{
    background: {_BG_SIDEBAR} !important;
    border-right: 1px solid {_BORDER} !important;
}}
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] .stMarkdown p,
section[data-testid="stSidebar"] .stCaption,
section[data-testid="stSidebar"] span {{
    color: {_GREEN_DIM} !important;
}}
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 {{
    color: {_GREEN} !important;
}}

/* ── Primary button ──────────────────────────────────────────────────────── */
.stButton > button {{
    background: {_GREEN} !important;
    color: #000 !important;
    border-radius: 4px !important;
    font-weight: 700 !important;
    border: none !important;
    font-family: {_FONT} !important;
    padding: 0.55rem 1.1rem !important;
    transition: background 0.15s ease !important;
}}
.stButton > button:hover {{
    background: {_GREEN_LIGHT} !important;
}}

/* ── Download button ─────────────────────────────────────────────────────── */
.stDownloadButton > button {{
    background: #166534 !important;
    color: #CCFFCC !important;
    border-radius: 4px !important;
    font-weight: 700 !important;
    border: 1px solid {_GREEN} !important;
    font-family: {_FONT} !important;
}}
.stDownloadButton > button:hover {{
    background: #15803D !important;
}}

/* ── Streamlit metric tiles ──────────────────────────────────────────────── */
[data-testid="metric-container"] {{
    background: {_BG_CARD} !important;
    border: 1px solid {_BORDER} !important;
    border-radius: 4px !important;
    padding: 0.9rem 1rem !important;
}}
[data-testid="stMetricLabel"] > div {{
    font-size: 0.72rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.07em !important;
    color: {_GREEN_MUTED} !important;
    font-weight: 600 !important;
    font-family: {_FONT} !important;
}}
[data-testid="stMetricValue"] > div {{
    font-size: 1.55rem !important;
    font-weight: 700 !important;
    color: {_GREEN} !important;
    font-family: {_FONT} !important;
}}
[data-testid="stMetricDelta"] > div {{
    font-size: 0.78rem !important;
    font-family: {_FONT} !important;
}}

/* ── Expanders ───────────────────────────────────────────────────────────── */
[data-testid="stExpander"] {{
    border: 1px solid {_BORDER} !important;
    border-radius: 4px !important;
}}

/* ── Custom KPI card class (use kpi_card() helper) ───────────────────────── */
.kpi-card {{
    background: {_BG_CARD};
    border: 1px solid {_BORDER};
    border-radius: 4px;
    padding: 1rem 0.8rem;
    text-align: center;
}}
.kpi-card .val  {{ font-size:1.55rem; font-weight:700; color:{_GREEN}; line-height:1.1; font-family:{_FONT}; }}
.kpi-card .unit {{ font-size:0.72rem; color:{_GREEN_MUTED}; margin-top:0.1rem; }}
.kpi-card .lbl  {{ font-size:0.78rem; color:{_GREEN_DIM}; margin-top:0.2rem; }}

/* ── Annotation block ────────────────────────────────────────────────────── */
.ann {{
    border-left: 2px solid {_BORDER};
    padding: 6px 12px;
    margin: 0.25rem 0 1.5rem 0;
    font-size: 0.8rem;
    color: {_TEXT_MUTED};
    line-height: 1.65;
}}
.ann strong {{ color: {_GREEN_DIM}; font-weight: 600; }}

/* ── Warning annotation ──────────────────────────────────────────────────── */
.ann-warn {{
    border-left: 2px solid #FCA5A5;
    padding: 6px 12px;
    margin: 0.25rem 0 1.5rem 0;
    font-size: 0.8rem;
    color: #FCA5A5;
    line-height: 1.65;
    background: #1A0D0D;
    border-radius: 0 4px 4px 0;
}}
.ann-warn strong {{ color: #FCA5A5; font-weight: 600; }}

/* ── Section label ───────────────────────────────────────────────────────── */
.lbl {{
    font-size: 0.68rem;
    font-weight: 700;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: {_TEXT_MUTED};
    margin: 2.5rem 0 0.4rem 0;
    display: block;
}}
</style>
"""


def apply_theme() -> None:
    """Inject the global dark-terminal CSS into the current Streamlit page.

    Call once near the top of each app, after st.set_page_config().
    """
    st.markdown(_CSS, unsafe_allow_html=True)


def page_header(title: str, subtitle: str = "") -> None:
    """Render the standard dark-green terminal-style page header.

    Parameters
    ----------
    title : str
        Main heading — shown in ALL CAPS with a > prompt prefix.
    subtitle : str
        Optional second line in a smaller, dimmer font.
    """
    sub_html = (
        f'<br><span style="font-size:1.0rem; font-weight:400; color:{_GREEN_DIM};">'
        f"{subtitle}</span>"
        if subtitle
        else ""
    )
    st.markdown(
        f"""
        <div style="background:{_BG_CARD}; border:1px solid {_GREEN};
                    border-radius:4px; padding:1.2rem 1.8rem; margin-bottom:1.2rem;">
          <h1 style="font-size:1.7rem; font-weight:700; color:{_GREEN}; margin:0;
                     font-family:{_FONT}; line-height:1.2; letter-spacing:0.02em;">
            &gt; {title.upper()}_
            {sub_html}
          </h1>
        </div>
        """,
        unsafe_allow_html=True,
    )


def kpi_card(value: str, unit: str, label: str) -> str:
    """Return HTML for a KPI card (pass to st.markdown with unsafe_allow_html=True).

    Example
    -------
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(kpi_card("4.2", "GWh/yr", "Annual Energy"), unsafe_allow_html=True)
    """
    return (
        f'<div class="kpi-card">'
        f'<div class="val">{value}</div>'
        f'<div class="unit">{unit}</div>'
        f'<div class="lbl">{label}</div>'
        f"</div>"
    )
