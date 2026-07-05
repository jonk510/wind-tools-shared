# wind-tools-shared

Shared library backing all the wind/solar Streamlit tools. Installed by each
tool via a pinned `git+https://…wind-tools-shared.git@<commit>` in its
`requirements.txt`. **Current pin: `6227f2f`.**

## Modules
- `style.py` — `apply_theme()`, `page_header()`, `plotly_dark_layout()` (the
  dark terminal-green brand; single source of the component CSS).
- `srtm.py` — `fetch_srtm_elevation`, `fetch_point_elevation` (OpenTopoData;
  bounded caches + per-batch retry).
- `timezone_lookup.py` — `get_timezone(lat, lon)` (TimezoneFinder wrapper).
- `csv_loader.py` — `load_csv` (BOM strip + delimiter auto-detect).
- `geo_loaders.py` — shapefile / KMZ point loaders.
- `epsg_selector.py` — Streamlit EPSG picker with MGA presets.
- `wtg_presets.py` — power curves + WTG acoustic spectra (from `data/*.xlsx`).
- `fulcrum/` — Fulcrum3D SODAR/FlightDECK loader subpackage.
- `tests/self_check.py` — offline checks for the pure-logic helpers.

## Test
- `python tests/self_check.py` (run from repo root — the parent dir must be on
  the path since this repo *is* the `shared` package).

## Packaging gotchas (critical)
- Modules live at the **repo root** (flat), mapped via
  `[tool.setuptools] packages=["shared","shared.fulcrum"]` +
  `[tool.setuptools.package-dir] shared="."`. Build backend MUST be
  `setuptools.build_meta`.
- **Any new subpackage** must be added to `packages` explicitly, or pip won't
  install it. Verify: `pip install --no-deps --target /tmp/x .` then check subdir.
- `data/*.xlsx` ships via `[tool.setuptools.package-data]`.

## Deploy workflow (changing shared)
1. Commit + push shared. 2. Repin each dependent's `requirements.txt` to the new
commit. 3. Commit + push each dependent (Streamlit Cloud re-clones HEAD of the
pinned URL). The 8 remote tools are currently all on `6227f2f`.
