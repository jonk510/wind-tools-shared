"""
Shared SRTM elevation downloader — OpenTopoData API (srtm30m dataset).

fetch_srtm_elevation(wtg_xy, epsg_code, buffer_m, grid_n)
    Downloads a regular grid of SRTM elevations around a set of projected XY
    coordinates and returns a DataFrame with columns X, Y, Z.
    Results are Streamlit-cached so re-runs with identical inputs skip the API.
"""

import time

import numpy as np
import pandas as pd
import streamlit as st

try:
    import requests
    from pyproj import Transformer as _ProjTransformer
    _HAS_DEPS = True
except ImportError:
    _HAS_DEPS = False


@st.cache_data(show_spinner=False)
def fetch_srtm_elevation(
    wtg_xy: np.ndarray,
    epsg_code: int,
    buffer_m: float = 5000.0,
    grid_n: int = 35,
) -> pd.DataFrame:
    """Download SRTM 30 m elevation over the WTG bounding box via OpenTopoData.

    Parameters
    ----------
    wtg_xy : ndarray (N, 2)
        Projected XY coordinates (metres) in *epsg_code* CRS.
    epsg_code : int
        EPSG code for wtg_xy.
    buffer_m : float
        Extra distance (m) added around the bounding box on each side.
    grid_n : int
        Number of grid points per axis (total API calls = ceil(grid_n² / 100)).

    Returns
    -------
    pd.DataFrame with columns X, Y, Z (projected coords + elevation in metres).
    """
    if not _HAS_DEPS:
        raise ImportError("Install 'requests' and 'pyproj':  pip install requests pyproj")

    xmin = wtg_xy[:, 0].min() - buffer_m
    xmax = wtg_xy[:, 0].max() + buffer_m
    ymin = wtg_xy[:, 1].min() - buffer_m
    ymax = wtg_xy[:, 1].max() + buffer_m

    xi = np.linspace(xmin, xmax, grid_n)
    yi = np.linspace(ymin, ymax, grid_n)
    xx, yy = np.meshgrid(xi, yi)
    grid_xy = np.column_stack([xx.ravel(), yy.ravel()])

    transformer = _ProjTransformer.from_crs(
        f"EPSG:{epsg_code}", "EPSG:4326", always_xy=True
    )
    lons, lats = transformer.transform(grid_xy[:, 0], grid_xy[:, 1])

    if not (np.all(np.isfinite(lons)) and np.all(np.isfinite(lats))):
        raise ValueError(
            f"Coordinate transformation failed (EPSG:{epsg_code} → WGS84 produced "
            f"non-finite values). Check that the EPSG code matches the coordinate "
            f"system of your WTG file."
        )

    elevations = []
    batch_size = 100
    n_pts = len(lats)
    for start in range(0, n_pts, batch_size):
        batch_lats = lats[start : start + batch_size]
        batch_lons = lons[start : start + batch_size]
        locations = "|".join(
            f"{lat:.6f},{lon:.6f}" for lat, lon in zip(batch_lats, batch_lons)
        )
        resp = requests.get(
            f"https://api.opentopodata.org/v1/srtm30m?locations={locations}",
            timeout=30,
        )
        resp.raise_for_status()
        for r in resp.json()["results"]:
            elev = r.get("elevation")
            elevations.append(float(elev) if elev is not None else 0.0)
        if start + batch_size < n_pts:
            time.sleep(1.1)  # OpenTopoData free-tier rate limit

    return pd.DataFrame(
        {"X": grid_xy[:, 0], "Y": grid_xy[:, 1], "Z": np.array(elevations)}
    )


@st.cache_data(show_spinner=False)
def fetch_point_elevation(lat: float, lon: float) -> int:
    """Return SRTM 30 m elevation (metres) for a single WGS84 lat/lon.

    Returns 0 on API error.  Result is Streamlit-cached.
    """
    if not _HAS_DEPS:
        return 0
    try:
        import requests as _req
        r = _req.get(
            "https://api.opentopodata.org/v1/srtm30m",
            params={"locations": f"{lat},{lon}"},
            timeout=10,
        )
        r.raise_for_status()
        elev = r.json()["results"][0]["elevation"]
        return int(round(elev)) if elev is not None else 0
    except Exception:
        return 0
