"""
Self-check regression tests for the wind-tools shared library.

Run from the repo root with:

    python tests/self_check.py

Offline — no network. Exits non-zero on any failure. This library is the
foundation of all 11 deployed tools, so a regression here breaks everything;
these lock the pure-logic helpers.
"""

import io
import os
import sys
import traceback

# This repo IS the `shared` package (root-mapped via package-dir), so its PARENT
# directory must be on the path to `import shared.*`.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

FAILURES: list[str] = []


def check(name):
    def wrap(fn):
        try:
            fn()
            print(f"  PASS  {name}")
        except Exception:
            FAILURES.append(name)
            print(f"  FAIL  {name}")
            traceback.print_exc()
        return fn
    return wrap


@check("csv_loader: BOM strip + delimiter auto-detect (comma/semicolon/tab)")
def _():
    from shared.csv_loader import load_csv
    # UTF-8 BOM + comma
    d1 = load_csv(b"\xef\xbb\xbfX,Y\n1,2\n3,4")
    assert list(d1.columns) == ["X", "Y"] and d1.shape == (2, 2)
    # semicolon
    d2 = load_csv(b"X;Y\n1;2")
    assert list(d2.columns) == ["X", "Y"] and int(d2.iloc[0]["Y"]) == 2
    # tab
    d3 = load_csv(b"X\tY\n5\t6")
    assert list(d3.columns) == ["X", "Y"] and int(d3.iloc[0]["X"]) == 5


@check("csv_loader: file-like source is rewound after read")
def _():
    from shared.csv_loader import load_csv
    buf = io.BytesIO(b"A,B\n1,2")
    load_csv(buf)
    assert buf.tell() == 0, "source not rewound — a second read would fail"


@check("timezone_lookup: known coordinates and international-waters fallback")
def _():
    from shared.timezone_lookup import get_timezone
    try:
        import timezonefinder  # noqa: F401
    except ImportError:
        return  # optional dependency absent — skip
    assert get_timezone(-31.95, 115.86) == "Australia/Perth"
    assert get_timezone(-34.93, 138.60) == "Australia/Adelaide"
    # Mid-Atlantic (no land timezone) → fallback
    assert get_timezone(0.0, -30.0, fallback="UTC") == "UTC"


@check("epsg_selector: MGA presets are valid, distinct EPSG codes")
def _():
    from shared.epsg_selector import _MGA_PRESETS
    codes = list(_MGA_PRESETS.values())
    assert len(codes) == len(set(codes)), "duplicate EPSG codes in presets"
    # GDA94 MGA zones are 283xx; WGS84 is 4326
    for c in codes:
        assert c == 4326 or 28349 <= c <= 28356, c


@check("wtg_presets: loader returns a dict without raising")
def _():
    from shared.wtg_presets import load_wtg_presets
    presets = load_wtg_presets()
    assert isinstance(presets, dict)


@check("style: apply_theme / page_header / plotly_dark_layout are importable")
def _():
    from shared import style
    for fn in ("apply_theme", "page_header", "plotly_dark_layout"):
        assert callable(getattr(style, fn)), fn


@check("fulcrum subpackage imports (packaging sanity)")
def _():
    import shared.fulcrum  # noqa: F401
    from shared.fulcrum import load_fulcrum_wind, wind_speed_series  # noqa: F401


print()
if FAILURES:
    print(f"{len(FAILURES)} check(s) FAILED: {', '.join(FAILURES)}")
    sys.exit(1)
print("All self-checks passed.")
