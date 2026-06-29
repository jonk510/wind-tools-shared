"""
Shared WTG acoustic spectra preset loader.

load_wtg_presets(spectra_file)
    Reads an Excel workbook where each sheet is one WTG model.
    Returns {display_name: (data_dict {freq_Hz: Lwa_dB}, is_third_octave)}.

The caller passes the path to their own copy of the Excel file so this module
stays independent of any single tool's directory layout.
"""

import os

import pandas as pd
import streamlit as st


@st.cache_data(show_spinner=False)
def load_wtg_presets(spectra_file: str) -> dict:
    """Return {display_name: (data_dict {freq: Lwa_dB}, is_third_oct)}.

    Parameters
    ----------
    spectra_file : str
        Absolute path to the WTG acoustic spectra Excel workbook.
    """
    if not os.path.exists(spectra_file):
        return {}
    try:
        xl = pd.ExcelFile(spectra_file)
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
            _OCTAVE_SET = {63.0, 125.0, 250.0, 500.0, 1000.0, 2000.0, 4000.0, 8000.0}
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
