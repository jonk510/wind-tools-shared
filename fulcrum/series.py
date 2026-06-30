"""
High-level Fulcrum3D ingestion helpers.

These wrap the low-level file_detector + data_loader so any tool can turn a set
of uploaded Fulcrum3D files into a usable wind-speed time series with a couple of
calls — e.g. the ERA5 × GWA calibration page uses a SODAR record as measured data.
"""

import pandas as pd

from .file_detector import unpack_upload
from .data_loader import route_and_load, merge_wind_datasets


def load_fulcrum_wind(uploaded_files):
    """Unpack + parse uploaded Fulcrum3D files and return a merged wind dataset.

    Parameters
    ----------
    uploaded_files : list
        Streamlit UploadedFile objects (CSV or ZIP) or pathlib.Path objects.

    Returns
    -------
    (wind_ds, info)
        wind_ds : dict {df, heights, meta, is_raw, versions} or None if no wind
                  profile data was found.
        info    : dict with keys n_wind_files, versions, unknown (list of
                  (filename, error)), met (bool — whether met/combined data was
                  also present).
    """
    all_files = unpack_upload(uploaded_files)
    wind_list, unknown, has_met = [], [], False
    for fname, lines in all_files:
        try:
            res = route_and_load(fname, lines)
        except Exception as e:           # noqa: BLE001 — surface per-file, keep going
            unknown.append((fname, str(e)))
            continue
        if res["type"] == "wind":
            wind_list.append(res["wind"])
        elif res["type"] in ("met", "combined"):
            has_met = True

    if not wind_list:
        return None, {"n_wind_files": 0, "versions": [], "unknown": unknown, "met": has_met}

    merged = merge_wind_datasets(wind_list)
    info = {
        "n_wind_files": len(wind_list),
        "versions": merged.get("versions", []),
        "unknown": unknown,
        "met": has_met,
    }
    return merged, info


def wind_speed_series(wind_ds, height, version=None):
    """Extract a tz-naive wind-speed Series (m/s) at `height` from a wind dataset.

    Parameters
    ----------
    wind_ds : dict
        A wind dataset as returned by load_fulcrum_wind / merge_wind_datasets.
    height : int
        Measurement height in metres (one of wind_ds["heights"]).
    version : str, optional
        For multi-version merged datasets, the algorithm version to pull from
        (e.g. "V3.6.1"). Defaults to the first available matching column.

    Returns
    -------
    pd.Series named 'wind_speed' (UTC, tz-naive datetime index), or None if no
    matching column is found.
    """
    df = wind_ds["df"]
    base = f"WS_{int(height)} [m/s]"
    versions = wind_ds.get("versions", []) or []

    candidates = []
    if version:
        candidates.append(f"{version.replace('.', '')}_{base}")
    candidates.append(base)                                  # single-version case
    candidates += [f"{v.replace('.', '')}_{base}" for v in versions]  # merged frames

    col = next((c for c in candidates if c in df.columns), None)
    if col is None:                                          # last-resort suffix match
        col = next((c for c in df.columns if c.endswith(base)), None)
    if col is None:
        return None

    s = pd.to_numeric(df[col], errors="coerce").dropna()
    s = s[(s >= 0.0) & (s <= 75.0)]                          # drop sentinels (999/9999)
    if getattr(s.index, "tz", None) is not None:
        s = s.tz_localize(None)
    s.name = "wind_speed"
    return s
