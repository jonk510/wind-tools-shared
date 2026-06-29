"""
Shared geographic file loaders — shapefile (geopandas) and KMZ/KML (xml).

Both functions return (xy: np.ndarray shape (N,2), names: list[str]) in the
caller's projected coordinate system, or (None, None) on error.
"""

import io
import os
import tempfile

import numpy as np
import streamlit as st


def load_shapefile_points(uploaded_files, target_epsg: int):
    """Write uploaded shapefile parts to a temp dir, read with geopandas, return (xy, names)."""
    try:
        import geopandas as gpd
    except ImportError:
        st.error("Install `geopandas` to use shapefile upload.")
        return None, None

    with tempfile.TemporaryDirectory() as tmp:
        for f in uploaded_files:
            with open(os.path.join(tmp, f.name), "wb") as fh:
                fh.write(f.read())
        shp_files = [p for p in os.listdir(tmp) if p.endswith(".shp")]
        if not shp_files:
            st.error("No .shp file found in the uploaded set.")
            return None, None
        gdf = gpd.read_file(os.path.join(tmp, shp_files[0]))

    gdf = gdf[gdf.geometry.notnull()]
    gdf = gdf[gdf.geometry.geom_type.isin(["Point", "MultiPoint"])]
    if gdf.empty:
        st.error("Shapefile contains no point features.")
        return None, None

    gdf = gdf.to_crs(epsg=target_epsg)
    xy = np.column_stack([gdf.geometry.x, gdf.geometry.y])
    name_col = next(
        (c for c in gdf.columns if c.lower() in ("name", "label", "id", "receptor")),
        None,
    )
    names = (
        gdf[name_col].astype(str).tolist()
        if name_col
        else [f"R{i+1}" for i in range(len(xy))]
    )
    return xy, names


def load_kmz_points(uploaded_file, target_epsg: int):
    """Parse a KMZ or KML file and return (xy, names) reprojected to target_epsg."""
    import zipfile
    import xml.etree.ElementTree as ET
    from pyproj import Transformer

    raw = uploaded_file.read()

    if zipfile.is_zipfile(io.BytesIO(raw)):
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            kml_names = [n for n in z.namelist() if n.lower().endswith(".kml")]
            if not kml_names:
                st.error("No KML found inside KMZ.")
                return None, None
            kml_bytes = z.read(kml_names[0])
    else:
        kml_bytes = raw

    root = ET.fromstring(kml_bytes)

    # Strip all namespace prefixes so tags become plain local names
    for elem in root.iter():
        if "}" in elem.tag:
            elem.tag = elem.tag.split("}", 1)[1]

    lons, lats, names = [], [], []
    for pm in root.iter("Placemark"):
        pt = pm.find(".//Point")
        if pt is None:
            continue
        coords_el = pt.find("coordinates")
        if coords_el is None or not coords_el.text:
            continue
        parts = coords_el.text.strip().split(",")
        lons.append(float(parts[0]))
        lats.append(float(parts[1]))
        name_el = pm.find("name")
        names.append(
            name_el.text.strip()
            if name_el is not None and name_el.text
            else f"P{len(lons)}"
        )

    if not lons:
        st.error("No point features found in KMZ/KML.")
        return None, None

    transformer = Transformer.from_crs("EPSG:4326", f"EPSG:{target_epsg}", always_xy=True)
    xs, ys = transformer.transform(lons, lats)
    return np.column_stack([xs, ys]), names
