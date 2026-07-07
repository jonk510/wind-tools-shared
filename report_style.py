"""
Shared PDF **report** template — deep-pine + emerald brand.

This is the single source of the *print* look for every wind/solar tool that
generates a matplotlib ``PdfPages`` report (ERA5×GWA wind, solar+battery, …).
It is the print-side sibling of :mod:`shared.style` (the on-screen Streamlit
dark-green theme): change a colour / font / rule weight here and every tool's
generated PDF updates the next time it is built.

What lives here
---------------
* **Design tokens** — the colour palette (``PINE``, ``GREEN``, …), page geometry
  (``A4_PORTRAIT`` / ``A4_LANDSCAPE``, ``MARGIN_L`` / ``MARGIN_R`` / ``CONTENT_W``),
  the resource colormap, and the matplotlib ``RCPARAMS`` font stack.
* **Layout primitives** — orientation-agnostic helpers that draw onto a figure in
  fractional (0–1) coordinates: :func:`page_chrome`, :func:`section_band`,
  :func:`h1` / :func:`h2`, :func:`para`, :func:`bullet`, :func:`equation`,
  :func:`render_table`, :func:`chart_style`, plus the low-level :func:`panel` /
  :func:`rule`.

What does NOT live here
-----------------------
The *content* of a report — which disclaimer, which section titles, which charts
— stays in each tool's own report generator. Each tool composes its pages from
these primitives, passing in its own text. That keeps the styling shared while
letting every report say the right thing.

Usage
-----
    from shared.report_style import (
        PINE, GREEN, A4_PORTRAIT, MARGIN_L as ML, CONTENT_W as AVAIL,
        apply_rcparams, new_page, page_chrome, section_band, h1, para,
        bullet, render_table, chart_style,
    )
    apply_rcparams()                 # once, at import
    fig = new_page(A4_PORTRAIT)
    page_chrome(fig, header_left="MY TOOL  ·  REPORT", section="Introduction",
                page_label="3", disclaimer="Indicative only.")
    y = section_band(fig, 0.94, 0.05, "1  Introduction")
    y = para(fig, y - 0.03, "Body text …")

All primitives take fractional figure coordinates, so the same helpers render
correctly on portrait *and* landscape pages.
"""

import textwrap

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

# ── Design tokens: colour palette ─────────────────────────────────────────────
# Deep pine + emerald accent — a print-friendly take on the tools' on-screen
# terminal-green brand. Edit these to restyle every report at once.
BLACK   = "#101614"
BODY    = "#26332C"   # body text
BORDER  = "#D9E3DC"   # hairline rules / table gridlines
CAPTION = "#55645B"   # captions
WHITE   = "#FFFFFF"
LIGHT   = "#F2F7F3"
MIDGREY = "#7C8A81"   # muted / running-header text
NAVY    = "#1C5E40"   # primary emphasis / chart series (forest green)
SLATE   = "#93A99B"   # secondary chart series (sage)
AMBER   = "#C4841D"
RED     = "#B4423A"
TEAL    = "#31816B"
PINE    = "#12382A"   # darkest brand green — bands, cover, table headers
GREEN   = "#2FA96C"   # bright accent — rules, chips, markers
MINT    = "#EAF4ED"   # tinted panel fill
ZEBRA   = "#F3F9F5"   # alternating table row fill

# ── Design tokens: page geometry ──────────────────────────────────────────────
A4_PORTRAIT  = (8.27, 11.69)
A4_LANDSCAPE = (11.69, 8.27)
MARGIN_L     = 0.095            # left content margin  (fraction of page width)
MARGIN_R     = 0.905           # right content margin
CONTENT_W    = MARGIN_R - MARGIN_L

# ── Design tokens: resource colormap (red → amber → green) ────────────────────
# Used for choropleth/scatter maps of a resource metric (wind speed, yield, …).
RESOURCE_CMAP = LinearSegmentedColormap.from_list(
    "resource", ["#DC2626", "#FBBF24", "#16A34A"], N=256
)

# ── Design tokens: matplotlib font stack ──────────────────────────────────────
RCPARAMS = {
    "font.family":      "sans-serif",
    "font.sans-serif":  ["Arial", "Liberation Sans", "Helvetica", "DejaVu Sans"],
    "font.size":        9,
    "axes.titlesize":   9,
    "axes.titleweight": "bold",
    "axes.labelsize":   8,
    "xtick.labelsize":  7.5,
    "ytick.labelsize":  7.5,
    "legend.fontsize":  7.5,
    "figure.facecolor": "white",
}


def apply_rcparams():
    """Apply the shared report font stack to matplotlib's global rcParams.

    Call once when a report module is imported. Import ``matplotlib`` and set the
    ``Agg`` backend first (reports are always rendered head-less).
    """
    import matplotlib
    matplotlib.rcParams.update(RCPARAMS)


# ── Low-level primitives ──────────────────────────────────────────────────────

def new_page(size=A4_PORTRAIT, facecolor="white"):
    """Create a blank report page (a matplotlib Figure) at the given size."""
    import matplotlib.pyplot as plt
    return plt.figure(figsize=size, facecolor=facecolor)


def panel(fig, rect, color):
    """A decorative colored axes (background panel / rule) that reliably renders.

    ``rect`` is ``[x0, y0, w, h]`` in figure fractions.

    NOTE: ``ax.axis('off')`` also hides the axes patch, so ``set_facecolor``
    would be silently ignored — hide ticks and spines individually instead.
    """
    ax = fig.add_axes(rect)
    ax.set_facecolor(color)
    ax.set_xticks([])
    ax.set_yticks([])
    for s in ax.spines.values():
        s.set_visible(False)
    return ax


def rule(fig, y, color=BORDER, x0=None, width=None, lw=0.0008):
    """Draw a horizontal rule (thin filled panel) across the page at height ``y``."""
    x0    = x0    if x0    is not None else 0.0
    width = width if width is not None else 1.0
    panel(fig, [x0, y, width, lw], color)


def content_rule(fig, y):
    """A thin border-coloured rule spanning the content column only."""
    rule(fig, y, color=BORDER, x0=MARGIN_L, width=CONTENT_W)


# ── Page chrome (running header + footer) ─────────────────────────────────────

def page_chrome(fig, header_left="", section="", page_label="",
                disclaimer="", accent=GREEN):
    """Consistent running header + footer on every page.

    Draws a brand accent strip across the top, a running header
    (``header_left`` on the left, ``section`` on the right), and a footer with an
    optional ``disclaimer`` on the left and ``Page {page_label}`` on the right.
    Text is per-tool; the layout / colours are shared.
    """
    ML, MR, AVAIL = MARGIN_L, MARGIN_R, CONTENT_W

    # Brand accent strip across the very top of the page.
    rule(fig, 0.9955, color=accent, lw=0.0045)

    # Header.
    if header_left:
        fig.text(ML, 0.968, header_left, fontsize=6.5, color=MIDGREY, va="bottom")
    if section:
        fig.text(MR, 0.968, section, fontsize=7.5, color=PINE, va="bottom",
                 ha="right", fontweight="bold")
    rule(fig, 0.962, color=BORDER, x0=ML, width=AVAIL)

    # Footer — disclaimer left, page number right.
    rule(fig, 0.044, color=BORDER, x0=ML, width=AVAIL)
    if disclaimer:
        fig.text(ML, 0.038, disclaimer, fontsize=6, color=MIDGREY, va="top")
    if page_label:
        fig.text(MR, 0.038, f"Page {page_label}", fontsize=7, color=PINE,
                 va="top", ha="right", fontweight="bold")


def section_band(fig, y_top, height, title, subtitle="", number=""):
    """Deep-pine section-title band with a bright-green accent bar.

    Returns the y coordinate at the bottom of the band.
    """
    ML = MARGIN_L
    ax = panel(fig, [0, y_top - height, 1, height], PINE)
    # Accent bar just left of the content column.
    ax.add_patch(plt.Rectangle((ML - 0.014, 0.16), 0.005, 0.68,
                               transform=ax.transAxes, color=GREEN,
                               clip_on=False))
    t = f"{number}   {title}" if number else title
    ax.text(ML, 0.65 if subtitle else 0.50, t, transform=ax.transAxes,
            color=WHITE, fontsize=13, fontweight="bold", va="center")
    if subtitle:
        ax.text(ML, 0.24, subtitle, transform=ax.transAxes,
                color="#9DC4AF", fontsize=8.5, va="center")
    return y_top - height


def h1(fig, y, text, number=""):
    """Level-1 heading with a green-accented rule below. Returns new y."""
    ML, AVAIL = MARGIN_L, CONTENT_W
    label = f"{number}   {text}" if number else text
    fig.text(ML, y, label, fontsize=12.5, color=PINE, fontweight="bold", va="top")
    y -= 0.024
    rule(fig, y + 0.005, color=GREEN,  x0=ML,          width=0.052,         lw=0.0018)
    rule(fig, y + 0.005, color=BORDER, x0=ML + 0.052,  width=AVAIL - 0.052)
    return y - 0.012


def h2(fig, y, text):
    """Level-2 heading. Returns new y."""
    fig.text(MARGIN_L, y, text, fontsize=10.5, color=NAVY, fontweight="bold", va="top")
    return y - 0.020


def para(fig, y, text, width=94, size=9.0, indent=0):
    """Wrap and render a paragraph. Honours embedded newlines. Returns new y."""
    x = MARGIN_L + indent
    for raw in text.split("\n"):
        for line in textwrap.wrap(raw, width - int(indent * 130)) or [""]:
            if y < 0.055:
                return y
            fig.text(x, y, line, fontsize=size, color=BODY, va="top")
            y -= 0.0155
        y -= 0.005
    return y


def bullet(fig, y, text, width=90):
    """Render a green-marker bullet point. Returns new y."""
    ML = MARGIN_L
    lines = textwrap.wrap(text, width)
    if not lines:
        return y
    fig.text(ML + 0.010, y, "•", fontsize=9, color=GREEN, va="top", fontweight="bold")
    fig.text(ML + 0.022, y, lines[0], fontsize=9, color=BODY, va="top")
    y -= 0.0155
    for cont in lines[1:]:
        fig.text(ML + 0.022, y, cont, fontsize=9, color=BODY, va="top")
        y -= 0.0155
    return y


def equation(fig, y, eq, note=""):
    """Render a centred equation block with an optional 'where …' note.

    Rendered as plain centred italic text — no surrounding box.
    """
    ML = MARGIN_L
    fig.text(0.5, y, eq, fontsize=9.5, color=PINE,
             va="top", ha="center", fontstyle="italic")
    y -= 0.024
    if note:
        for line in textwrap.wrap(f"where  {note}", 108):
            fig.text(ML + 0.015, y, line, fontsize=8, color=MIDGREY, va="top")
            y -= 0.014
        y -= 0.004
    return y - 0.006


def chart_style(ax):
    """Apply the shared chart look (no top/right spines, soft green grid)."""
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(True, alpha=0.5, lw=0.5, color="#E2EAE4")
    ax.tick_params(labelsize=7.5)


# ── Table renderer ────────────────────────────────────────────────────────────

def render_table(fig, rows, col_specs, y_start, caption="", y_min=0.08,
                 fmt=None, right_align=frozenset(), emphasis_key=None):
    """Render a styled data table: pine header band, zebra rows.

    Parameters
    ----------
    rows : list of dict
        One dict per row, keyed by the column keys in ``col_specs``.
    col_specs : list of (key, header_label, relative_width)
        ``header_label`` may contain ``\\n`` for a two-line header.
    fmt : callable ``(value, key) -> str``, optional
        Per-cell formatter. Defaults to ``str`` (with ``None``/NaN → "–").
    right_align : set of keys
        Column keys to right-align (numeric columns line up when scanning down).
    emphasis_key : key, optional
        Column rendered bold in the pine accent colour (e.g. a row-label column).

    Returns ``(final_y, overflow_rows)`` — any rows that did not fit are returned
    so the caller can continue them on a fresh page.
    """
    ML, AVAIL = MARGIN_L, CONTENT_W
    if fmt is None:
        def fmt(val, key):
            if val is None or (isinstance(val, float) and np.isnan(val)):
                return "–"
            return str(val)

    keys   = [c[0] for c in col_specs]
    labels = [c[1] for c in col_specs]
    rel_w  = [c[2] for c in col_specs]
    total  = sum(rel_w)
    col_w  = [w / total for w in rel_w]     # fractions of table width

    HDR_H = 0.034
    ROW_H = 0.025

    y = y_start

    if caption:
        fig.text(ML, y, caption, fontsize=8.5, color=PINE,
                 va="top", fontweight="bold")
        y -= 0.020

    # Header band.
    ax_h = panel(fig, [ML, y - HDR_H, AVAIL, HDR_H], PINE)
    xf = 0.0
    for key, lbl, cw in zip(keys, labels, col_w):
        right = key in right_align
        tx = xf + cw - 0.010 if right else xf + 0.010
        for li, line in enumerate(str(lbl).split("\n")):
            ax_h.text(tx, 0.70 - li * 0.36, line,
                      transform=ax_h.transAxes,
                      fontsize=7.5, color=WHITE, fontweight="bold",
                      va="top", ha="right" if right else "left")
        xf += cw
    y -= HDR_H

    overflow = []
    for ri, row in enumerate(rows):
        if y < y_min + ROW_H:
            overflow = rows[ri:]
            break
        ax_r = panel(fig, [ML, y - ROW_H, AVAIL, ROW_H],
                     WHITE if ri % 2 == 0 else ZEBRA)
        xf = 0.0
        for key, cw in zip(keys, col_w):
            txt   = fmt(row.get(key), key)
            right = key in right_align
            emph  = key == emphasis_key
            tx    = xf + cw - 0.010 if right else xf + 0.010
            ax_r.text(tx, 0.5, txt,
                      transform=ax_r.transAxes, fontsize=8,
                      color=PINE if emph else BODY,
                      va="center", ha="right" if right else "left",
                      fontweight="bold" if emph else "normal",
                      clip_on=True)
            xf += cw
        y -= ROW_H

    rule(fig, y - 0.0012, color=PINE, x0=ML, width=AVAIL, lw=0.0012)

    return y - 0.004, overflow
