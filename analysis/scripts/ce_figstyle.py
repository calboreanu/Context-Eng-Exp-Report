#!/usr/bin/env python3
"""Shared house style for the Context Engineering manuscript figures.

Design contract
---------------
Artwork is authored at Elsevier's full-width final size (190 mm = 7.4803 in),
laid out on an axes that fills the whole canvas, and saved WITHOUT
``bbox_inches="tight"`` so the emitted PDF is exactly 190 mm wide. The figure is
then included with ``width=\\linewidth``.

In the elsarticle preprint layout \\linewidth = 390 pt, so everything is scaled
by 390 / 538.58 = 0.724. ``FS_MIN`` (10.0 pt) therefore lands at 7.24 pt on the
page, which clears Elsevier's 7 pt minimum for normal lettering. At journal
production the same file placed at 190 mm renders at its authored size, so the
type only ever gets larger.

Visual language follows Figures 1-2: grayscale value tiers, square heavy
borders, bold sans headings over a thin rule, muted italic secondary text.
A single light blue accent is reserved for one job - marking the
context-engineering side of Figure 4 - and is never used decoratively.
"""
from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
matplotlib.rcParams["pdf.fonttype"] = 42          # embed TrueType, no Type 3
matplotlib.rcParams["ps.fonttype"] = 42
matplotlib.rcParams["font.family"] = "sans-serif"
matplotlib.rcParams["font.sans-serif"] = [
    "Liberation Sans",   # metrically identical to Arial
    "Arial",
    "Helvetica",
    "DejaVu Sans",
]

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyArrowPatch, Ellipse

# --------------------------------------------------------------------------
# Geometry
# --------------------------------------------------------------------------
MM = 1.0 / 25.4
FIG_W_IN = 190 * MM                 # 7.4803 in  = 538.58 pt  (Elsevier full width)
PREPRINT_LINEWIDTH_PT = 390.0       # elsarticle preprint text width
SCALE = PREPRINT_LINEWIDTH_PT / (FIG_W_IN * 72.0)   # 0.7241

# --------------------------------------------------------------------------
# Type scale. Authored sizes; the comment is the size on the preprint page.
# --------------------------------------------------------------------------
FS_TITLE = 15.0    # -> 10.9 pt
FS_HEAD = 12.5     # ->  9.1 pt
FS_BODY = 11.0     # ->  8.0 pt
FS_SEC = 10.4      # ->  7.5 pt
FS_MIN = 10.0      # ->  7.2 pt   <- floor, never go below this

# --------------------------------------------------------------------------
# Palette
# --------------------------------------------------------------------------
INK = "#1a1a1a"
MUTED = "#555555"
EDGE = "#333333"
RULE = "#9a9a9a"
DASH = "#6f6f6f"

TIER = ["#d9d9d9", "#d2d2d2", "#c9c9c9", "#bdbdbd"]   # Figure 1 value ramp
PALE = "#f1f1f1"
LIGHT = "#e6e6e6"
MID = "#d5d5d5"

ACCENT = "#cfdded"        # the single accent, Figure 4 only
ACCENT_EDGE = "#2f5677"

LW_BOX = 1.6
LW_BOX_HEAVY = 2.0
LW_RULE = 0.9


def new_canvas(height_in: float):
    """Full-bleed axes on a 190 mm wide canvas; returns (fig, ax) in 0-1 coords."""
    fig = plt.figure(figsize=(FIG_W_IN, height_in))
    ax = fig.add_axes((0, 0, 1, 1))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    ax._ce_height_in = height_in
    return fig, ax


def pt2y(ax, pts: float) -> float:
    """Convert points to axis-y units on this canvas."""
    return pts / 72.0 / ax._ce_height_in


def pt2x(pts: float) -> float:
    """Convert points to axis-x units on this canvas."""
    return pts / 72.0 / FIG_W_IN


def card(ax, x, y, w, h, fill=LIGHT, edge=EDGE, lw=LW_BOX, ls="solid", z=1):
    """Square-cornered panel, the house container."""
    ax.add_patch(Rectangle((x, y), w, h, facecolor=fill, edgecolor=edge,
                           linewidth=lw, linestyle=ls, zorder=z))


def rule(ax, x0, x1, y, color=RULE, lw=LW_RULE, z=3):
    ax.plot([x0, x1], [y, y], color=color, lw=lw, zorder=z, solid_capstyle="butt")


def arrow(ax, p0, p1, lw=2.0, color=INK, scale=15, ls="solid", z=4):
    ax.add_patch(FancyArrowPatch(p0, p1, arrowstyle="-|>", mutation_scale=scale,
                                 linewidth=lw, color=color, linestyle=ls,
                                 shrinkA=0, shrinkB=0, zorder=z))


def label(ax, x, y, s, *, size=FS_SEC, weight="normal", style="normal",
          color=INK, ha="left", va="center", mask=False, z=5, **kw):
    """Text with an optional white knockout so it can sit over a line."""
    bbox = None
    if mask:
        bbox = dict(boxstyle="square,pad=0.18", facecolor="white",
                    edgecolor="none")
    return ax.text(x, y, s, fontsize=size, fontweight=weight, fontstyle=style,
                   color=color, ha=ha, va=va, bbox=bbox, zorder=z, **kw)


def text_width_pt(fig, s, size, weight="normal", style="normal") -> float:
    """Measured width of a single line, in points at authored scale."""
    t = fig.text(0, 0, s, fontsize=size, fontweight=weight, fontstyle=style)
    fig.canvas.draw()
    bb = t.get_window_extent(renderer=fig.canvas.get_renderer())
    t.remove()
    return bb.width / fig.dpi * 72.0


def wrap_pt(fig, s, size, max_pt, weight="normal", style="normal") -> str:
    """Greedy word wrap to a measured width. Existing newlines are respected.

    Text that silently ran past its box was the single most common defect in
    the previous figure set, so widths are measured rather than estimated.
    """
    out = []
    for para in s.split("\n"):
        line, words = "", para.split()
        for w in words:
            trial = f"{line} {w}".strip()
            if line and text_width_pt(fig, trial, size, weight, style) > max_pt:
                out.append(line)
                line = w
            else:
                line = trial
        out.append(line)
    return "\n".join(out)


def badge(ax, x, y, n, *, d_pt=15.5, size=FS_SEC, fill="white", edge=INK, lw=1.4):
    """Numbered disc. Drawn rather than typed: Liberation Sans has no U+2460
    circled-digit glyphs, and a missing glyph is a silent blank in the PDF."""
    ax.add_patch(Ellipse((x, y), pt2x(d_pt), pt2y(ax, d_pt), facecolor=fill,
                         edgecolor=edge, linewidth=lw, zorder=4))
    ax.text(x, y, str(n), fontsize=size, fontweight="bold", color=edge,
            ha="center", va="center", zorder=5)


def save(fig, stem: str, outdir):
    """Emit vector PDF at exact authored size plus a 600 dpi JPG mirror."""
    from pathlib import Path

    outdir = Path(outdir)
    pdf = outdir / f"{stem}.pdf"
    jpg = outdir / f"{stem}.jpg"
    fig.savefig(pdf, facecolor="white")                      # no tight bbox
    fig.savefig(jpg, dpi=600, facecolor="white", pil_kwargs={"quality": 95})
    plt.close(fig)
    return pdf, jpg
