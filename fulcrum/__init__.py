"""
shared.fulcrum — Fulcrum3D SODAR/FlightDECK file loading.

Lifted from the SODAR Data Tool so multiple tools can ingest Fulcrum3D exports
(CSV or ZIP) without duplicating the parser. The SODAR tool uses the low-level
loaders for its cleaning pipeline; the ERA5 × GWA calibration page uses the
high-level helpers to turn a SODAR record into a measured wind-speed series.
"""

from .file_detector import (
    FileMetadata,
    detect_file,
    load_text_lines,
    unpack_upload,
)
from .data_loader import (
    route_and_load,
    merge_wind_datasets,
    load_wind_file,
    load_met_file,
    load_combined_alldata,
)
from .series import load_fulcrum_wind, wind_speed_series

__all__ = [
    "FileMetadata",
    "detect_file",
    "load_text_lines",
    "unpack_upload",
    "route_and_load",
    "merge_wind_datasets",
    "load_wind_file",
    "load_met_file",
    "load_combined_alldata",
    "load_fulcrum_wind",
    "wind_speed_series",
]
