"""
Shared EPSG coordinate-system selector widget for Streamlit sidebars.

epsg_selector(default_epsg, key)
    Renders a number_input for the EPSG code and a caption showing the CRS name.
    Returns the selected EPSG code as an int.
"""

import streamlit as st

# Australian MGA zone presets — shown as a quick-pick selectbox
_MGA_PRESETS = {
    "MGA Zone 49 (W.A. far west)": 28349,
    "MGA Zone 50 (W.A. west)":     28350,
    "MGA Zone 51 (W.A./S.A.)":     28351,
    "MGA Zone 52 (S.A./Vic/NSW)":  28352,
    "MGA Zone 53 (Vic/NSW/Qld)":   28353,
    "MGA Zone 54 (NSW/Qld)":       28354,
    "MGA Zone 55 (NSW/Qld east)":  28355,
    "MGA Zone 56 (Qld far east)":  28356,
    "WGS 84 geographic (deg)":      4326,
}


def epsg_selector(default_epsg: int = 28354, key: str = "epsg") -> int:
    """Render EPSG input widget and return the selected EPSG code.

    Parameters
    ----------
    default_epsg : int
        Initial value shown in the number input.
    key : str
        Streamlit widget key prefix (use a unique value if you have multiple
        selectors on the same page).

    Returns
    -------
    int  — the EPSG code chosen by the user.
    """
    # Quick-pick preset dropdown
    preset_labels = ["— type manually —"] + list(_MGA_PRESETS.keys())
    preset_choice = st.selectbox(
        "Quick-pick coordinate system",
        preset_labels,
        index=0,
        key=f"{key}_preset",
    )
    if preset_choice != "— type manually —":
        default_epsg = _MGA_PRESETS[preset_choice]

    epsg_code = st.number_input(
        "Coordinate System's EPSG code",
        value=int(default_epsg),
        min_value=1000,
        max_value=99999,
        step=1,
        key=f"{key}_input",
    )
    try:
        from pyproj import CRS
        st.caption(f"📐 {CRS.from_epsg(int(epsg_code)).name}")
    except Exception:
        st.caption("📐 (unknown CRS — check EPSG code)")

    return int(epsg_code)
