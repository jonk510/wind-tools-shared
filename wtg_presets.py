"""
Shared WTG data loaders.

load_power_curves()
    Reads the bundled power_curves.xlsx.
    Returns DataFrame[WTG → kW] indexed by wind speed (m/s), or None if missing.

load_wtg_presets()
    Reads the bundled WTG acoustic spectra workbook (one sheet per WTG model).
    Returns {display_name: (data_dict {freq_Hz: Lwa_dB}, is_third_octave)}.
    Pass spectra_file to override with a custom path.
"""

import os
from pathlib import Path

import pandas as pd
import streamlit as st

_DATA_DIR = Path(__file__).parent / "data"
_OCTAVE_SET = {63.0, 125.0, 250.0, 500.0, 1000.0, 2000.0, 4000.0, 8000.0}


@st.cache_data(show_spinner=False)
def load_power_curves() -> pd.DataFrame | None:
    """Return DataFrame[WTG → kW] indexed by wind speed (m/s), or None if file missing."""
    p = _DATA_DIR / "power_curves.xlsx"
    if not p.exists():
        return None
    df = pd.read_excel(p, index_col=0, header=0)
    df.index = df.index.astype(float)
    df.columns = [str(c).strip() for c in df.columns]
    return df.sort_index()


@st.cache_data(show_spinner=False)
def load_wtg_presets(spectra_file: str | None = None) -> dict:
    """Return {display_name: (data_dict {freq: Lwa_dB}, is_third_oct)}.

    Uses the bundled WTG_Acoustic_Spectra_Loudest_Modes workbook by default.
    Pass spectra_file to override with a custom path.
    """
    path = spectra_file or str(_DATA_DIR / "WTG_Acoustic_Spectra_Loudest_Modes 1.xlsx")
    if not os.path.exists(path):
        return {}
    try:
        xl = pd.ExcelFile(path)
        presets = {}
        for sheet in xl.sheet_names:
            df = xl.parse(sheet)
            freq_col = next((c for c in df.columns if "freq" in c.lower()), None)
            lw_col   = next((c for c in df.columns if "lw"   in c.lower()), None)
            if freq_col is None or lw_col is None:
                continue
            df = df.dropna(subset=[lw_col])
            if df.empty:
                continue
            data = {float(r[freq_col]): float(r[lw_col]) for _, r in df.iterrows()}
            is_third = any(f not in _OCTAVE_SET for f in data.keys())
            name = (
                sheet.replace("_1-3oct", "")
                     .replace("_1-1oct", "")
                     .replace("_", " ")
            )
            presets[name] = (data, is_third)
        return presets
    except Exception:
        return {}
