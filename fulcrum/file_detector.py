"""
Parses the Fulcrum3D FlightDECK file header to identify format, type, and version.
Handles zipped folders, separate files, and combined alldata CSVs.

Shared module — used by the SODAR Data Tool and the ERA5 × GWA calibration page.
"""

import io
import re
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


WIND_FILE_TYPES = {"v351", "v361", "v38881"}


@dataclass
class FileMetadata:
    source_path: str
    extract_format: str          # "raw" or "processed"
    data_types: list[str]        # e.g. ["wind_v361"], ["met"], ["wind_v351","met",...]
    algorithm_version: str       # e.g. "V3.6.1" or "" for non-wind
    timestamp_end_of_period: bool
    header_lines: int            # number of lines before the column header
    utc_offset_hours: float
    site: str
    serial: str
    location: str
    latitude: Optional[float]
    longitude: Optional[float]
    orientation: Optional[float]
    is_wind: bool = field(init=False)
    is_combined: bool = field(init=False)

    def __post_init__(self):
        self.is_wind = any(t.startswith("wind") for t in self.data_types)
        self.is_combined = len(self.data_types) > 1


def _parse_header_block(lines: list[str]) -> dict:
    """Extract key:value pairs from the | key:,,value header block."""
    meta = {}
    for line in lines:
        stripped = line.lstrip("|").strip()
        if ":,," in stripped:
            key, _, value = stripped.partition(":,,")
            meta[key.strip()] = value.strip()
    return meta


def _classify_data_type(type_str: str) -> list[str]:
    """
    Turn the 'Data type / version' string into a normalised list of type tokens.
    Handles combined strings like 'Met 10 min / System Status 10 min / ...'.
    """
    tokens = []
    for part in type_str.split("/"):
        p = part.strip().lower()
        if "wind profile" in p:
            # extract version number e.g. "v3.6.1" → "v361"
            m = re.search(r"v(\d+)\.(\d+)\.?(\d*)", p)
            if m:
                ver = "v" + m.group(1) + m.group(2) + (m.group(3) or "")
            else:
                ver = "vunknown"
            tokens.append(f"wind_{ver}")
        elif "met" in p:
            tokens.append("met")
        elif "system status" in p or "state" in p:
            tokens.append("state")
        elif "pyro" in p:
            tokens.append("pyro")
        elif "location" in p:
            tokens.append("location")
        elif "analog" in p:
            tokens.append("analog")
    return tokens if tokens else ["unknown"]


def _parse_utc_offset(offset_str: str) -> float:
    """'+8 Hours' → 8.0, '-5 Hours' → -5.0"""
    m = re.search(r"([+-]?\d+(?:\.\d+)?)\s*[Hh]", offset_str)
    return float(m.group(1)) if m else 0.0


def detect_file(text_lines: list[str], source_path: str = "") -> FileMetadata:
    """Inspect lines from a single Fulcrum3D CSV and return its FileMetadata."""
    header_block = []
    col_header_line = -1

    for i, line in enumerate(text_lines):
        if line.startswith("|") and "____" not in line:
            header_block.append(line)
        elif line.startswith("Timestamp_UTC"):
            col_header_line = i
            break

    meta = _parse_header_block(header_block)

    fmt_raw = meta.get("Extract format", "").lower()
    extract_format = "processed" if "processed" in fmt_raw else "raw"

    type_str = meta.get("Data type / version", "")
    data_types = _classify_data_type(type_str)

    alg_ver = ""
    if any(t.startswith("wind") for t in data_types):
        m = re.search(r"V(\d+\.\d+(?:\.\d+)?)", type_str)
        alg_ver = m.group(0) if m else ""

    ts_fmt = meta.get("Time stamp format", "").lower()
    end_of_period = "end" in ts_fmt

    utc_offset = _parse_utc_offset(meta.get("Local Time Offset Applied to UTC", "+0 Hours"))

    def _safe_float(s):
        try:
            return float(s)
        except (ValueError, TypeError):
            return None

    return FileMetadata(
        source_path=source_path,
        extract_format=extract_format,
        data_types=data_types,
        algorithm_version=alg_ver,
        timestamp_end_of_period=end_of_period,
        header_lines=col_header_line,
        utc_offset_hours=utc_offset,
        site=meta.get("Site", ""),
        serial=meta.get("Serial number", ""),
        location=meta.get("Location", ""),
        latitude=_safe_float(meta.get("Latitude")),
        longitude=_safe_float(meta.get("Longitude")),
        orientation=_safe_float(meta.get("Orientation")),
    )


def load_text_lines(file_obj) -> list[str]:
    """Read lines from a file-like object (bytes or text)."""
    if isinstance(file_obj, (bytes, bytearray)):
        file_obj = io.BytesIO(file_obj)
    if hasattr(file_obj, "read"):
        raw = file_obj.read()
        if isinstance(raw, bytes):
            raw = raw.decode("utf-8", errors="replace")
        return raw.splitlines(keepends=True)
    return list(file_obj)


def unpack_upload(uploaded_files: list) -> list[tuple[str, list[str]]]:
    """
    Given a list of Streamlit UploadedFile objects (or Path objects for testing),
    return a list of (filename, lines) tuples — unpacking any zip files along the way.
    """
    results = []
    for uf in uploaded_files:
        # Support both Streamlit UploadedFile and pathlib.Path (for tests)
        if isinstance(uf, Path):
            name = uf.name
            data = uf.read_bytes()
        else:
            name = uf.name
            data = uf.read()

        if name.lower().endswith(".zip"):
            with zipfile.ZipFile(io.BytesIO(data)) as zf:
                for member in zf.namelist():
                    # skip macOS metadata files and directories
                    if "__MACOSX" in member or member.endswith("/"):
                        continue
                    if not member.lower().endswith(".csv"):
                        continue
                    member_name = Path(member).name
                    with zf.open(member) as f:
                        lines = load_text_lines(f)
                    results.append((member_name, lines))
        elif name.lower().endswith(".csv"):
            lines = load_text_lines(io.BytesIO(data))
            results.append((name, lines))

    return results
