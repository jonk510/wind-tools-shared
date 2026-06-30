"""
Loads Fulcrum3D SODAR CSV files (raw or processed, separate or combined)
into a normalised internal structure.

Shared module — used by the SODAR Data Tool and the ERA5 × GWA calibration page.

Internal wind DataFrame columns per height H:
  WS_{H}, WD_{H}, WS_SD_{H}, VertWS_{H}, Inflow_{H}
  Filter1_{H}, Filter2_{H}, Filter3_{H}   (raw only — 1=good)
  SNR_{H}                                  (processed only)

Index: Timestamp_UTC (DatetimeIndex, UTC-normalised, end-of-period convention)
"""

import re
import io
import pandas as pd
import numpy as np
from .file_detector import FileMetadata, detect_file


# ── helpers ───────────────────────────────────────────────────────────────────

def _skip_to_header(lines: list[str]) -> int:
    """Return the index of the column-header line."""
    for i, line in enumerate(lines):
        if line.startswith("Timestamp_UTC"):
            return i
    raise ValueError("Could not find 'Timestamp_UTC' column header in file.")


def _parse_csv_from_lines(lines: list[str], header_idx: int) -> pd.DataFrame:
    text = "".join(lines[header_idx:])
    df = pd.read_csv(io.StringIO(text), dtype=str)
    # strip column name whitespace
    df.columns = [c.strip() for c in df.columns]
    return df


def _parse_timestamp(df: pd.DataFrame, end_of_period: bool, utc_offset: float) -> pd.Series:
    """Return a UTC DatetimeIndex from the Timestamp_UTC column."""
    ts = pd.to_datetime(df["Timestamp_UTC [DD/MM/YYYY hh:mm]"], dayfirst=True)
    if utc_offset != 0:
        # the column is already UTC despite the offset label (offset just tells
        # you the local time relationship), so no adjustment needed
        pass
    if not end_of_period:
        ts = ts + pd.Timedelta(minutes=10)
    return ts


def _extract_heights(columns: list[str]) -> list[int]:
    """Extract sorted list of measurement heights from column names."""
    heights = set()
    for c in columns:
        m = re.match(r"WS_(\d+)", c)
        if m:
            heights.add(int(m.group(1)))
    return sorted(heights)


def _normalise_raw_columns(df: pd.DataFrame, heights: list[int]) -> pd.DataFrame:
    """
    Raw files use WS_SD_{H} — already standard.
    Just cast numeric columns and replace blanks with NaN.
    """
    cols_to_num = []
    for h in heights:
        cols_to_num += [
            f"WS_{h} [m/s]", f"WD_{h} [deg]", f"WS_SD_{h} [m/s]",
            f"VertWS_{h} [m/s]", f"Inflow_{h} [deg]",
            f"Filter1_{h} [0/1]", f"Filter2_{h} [0/1]", f"Filter3_{h} [0/1]",
        ]
    for c in cols_to_num:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


def _normalise_processed_columns(df: pd.DataFrame, heights: list[int]) -> pd.DataFrame:
    """
    Processed files use WindSpeed_{H}_SD and SNR_{H} — rename to standard.
    Bad data is blank (NaN after parse).
    """
    rename = {}
    for h in heights:
        sd_col = f"WindSpeed_{h}_SD"
        if sd_col in df.columns:
            rename[sd_col] = f"WS_SD_{h} [m/s]"
    df = df.rename(columns=rename)

    cols_to_num = []
    for h in heights:
        cols_to_num += [
            f"WS_{h} [m/s]", f"WD_{h} [deg]", f"WS_SD_{h} [m/s]",
            f"VertWS_{h} [m/s]", f"Inflow_{h} [deg]",
            f"SNR_{h}",
        ]
    for c in cols_to_num:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


# ── public API ─────────────────────────────────────────────────────────────────

def load_wind_file(lines: list[str], meta: FileMetadata) -> dict:
    """
    Parse a single wind profile CSV (raw or processed).

    Returns dict with keys:
      df        – DataFrame indexed by UTC timestamp
      heights   – list of int heights
      meta      – FileMetadata
      is_raw    – bool
    """
    header_idx = _skip_to_header(lines)
    raw_df = _parse_csv_from_lines(lines, header_idx)

    heights = _extract_heights(raw_df.columns.tolist())
    if not heights:
        raise ValueError("No wind speed columns (WS_NNN) found — not a wind profile file?")

    is_raw = (meta.extract_format == "raw")

    if is_raw:
        raw_df = _normalise_raw_columns(raw_df, heights)
    else:
        raw_df = _normalise_processed_columns(raw_df, heights)

    ts = _parse_timestamp(raw_df, meta.timestamp_end_of_period, meta.utc_offset_hours)
    raw_df.index = ts
    raw_df.index.name = "Timestamp_UTC"

    # Drop the raw timestamp text columns to keep things tidy
    drop_cols = [c for c in raw_df.columns if c.startswith("Timestamp_") or c in ("Hour_UTC", "Hour_Local")]
    raw_df = raw_df.drop(columns=[c for c in drop_cols if c in raw_df.columns])

    return {"df": raw_df, "heights": heights, "meta": meta, "is_raw": is_raw}


def load_met_file(lines: list[str], meta: FileMetadata) -> pd.DataFrame:
    """Parse a Met ancillary CSV. Returns DataFrame indexed by UTC timestamp."""
    header_idx = _skip_to_header(lines)
    df = _parse_csv_from_lines(lines, header_idx)
    ts = _parse_timestamp(df, meta.timestamp_end_of_period, meta.utc_offset_hours)
    df.index = ts
    df.index.name = "Timestamp_UTC"
    drop_cols = [c for c in df.columns if c.startswith("Timestamp_") or c in ("Hour_UTC", "Hour_Local")]
    df = df.drop(columns=[c for c in drop_cols if c in df.columns])
    numeric_cols = [c for c in df.columns if c not in ("Timestamp_Local [DD/MM/YYYY hh:mm]",)]
    for c in numeric_cols:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


def load_combined_alldata(lines: list[str], meta: FileMetadata) -> pd.DataFrame:
    """
    Parse a combined alldata CSV (Met + State + Pyro + Location merged).
    This file never contains wind profile data.
    """
    header_idx = _skip_to_header(lines)
    df = _parse_csv_from_lines(lines, header_idx)
    ts = _parse_timestamp(df, meta.timestamp_end_of_period, meta.utc_offset_hours)
    df.index = ts
    df.index.name = "Timestamp_UTC"
    drop_cols = [c for c in df.columns if c.startswith("Timestamp_") or c in ("Hour_UTC", "Hour_Local")]
    df = df.drop(columns=[c for c in drop_cols if c in df.columns])
    for c in df.columns:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


def route_and_load(filename: str, lines: list[str]) -> dict:
    """
    Auto-detect file type and load appropriately.

    Returns dict with:
      type    – "wind" | "met" | "state" | "pyro" | "location" | "combined" | "unknown"
      meta    – FileMetadata
      wind    – dict from load_wind_file (if type=="wind")
      met_df  – DataFrame (if type in {"met","combined"})
      raw_df  – raw DataFrame for non-wind ancillary files
    """
    meta = detect_file(lines, source_path=filename)
    result = {"type": "unknown", "meta": meta, "filename": filename}

    if meta.is_combined:
        result["type"] = "combined"
        result["met_df"] = load_combined_alldata(lines, meta)
        return result

    if meta.is_wind:
        result["type"] = "wind"
        result["wind"] = load_wind_file(lines, meta)
        return result

    if "met" in meta.data_types:
        result["type"] = "met"
        result["met_df"] = load_met_file(lines, meta)
        return result

    # state / pyro / location — load as generic numeric DataFrame
    header_idx = _skip_to_header(lines)
    df = _parse_csv_from_lines(lines, header_idx)
    ts = _parse_timestamp(df, meta.timestamp_end_of_period, meta.utc_offset_hours)
    df.index = ts
    df.index.name = "Timestamp_UTC"
    result["type"] = meta.data_types[0] if meta.data_types else "unknown"
    result["raw_df"] = df
    return result


def merge_wind_datasets(wind_list: list[dict]) -> dict:
    """
    Merge multiple wind dataset dicts (e.g. V3.5.1 + V3.6.1 + V3.888) that
    share the same timestamp index into a single dict with a version-prefixed
    column namespace, plus a 'versions' list.
    """
    if len(wind_list) == 1:
        w = wind_list[0]
        w["versions"] = [w["meta"].algorithm_version]
        return w

    versions = [w["meta"].algorithm_version for w in wind_list]
    heights = wind_list[0]["heights"]
    is_raw = wind_list[0]["is_raw"]

    frames = {}
    for w in wind_list:
        ver = w["meta"].algorithm_version.replace(".", "")
        df = w["df"].add_prefix(f"{ver}_")
        frames[ver] = df

    combined = pd.concat(list(frames.values()), axis=1)

    return {
        "df": combined,
        "heights": heights,
        "meta": wind_list[0]["meta"],
        "is_raw": is_raw,
        "versions": versions,
        "version_frames": frames,
    }
