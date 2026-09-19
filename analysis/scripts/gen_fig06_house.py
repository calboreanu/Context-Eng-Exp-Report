#!/usr/bin/env python3
"""Figure 4 (file fig-06) - event-v5 analysis and interpretation boundary.

House-style rebuild driven by the corrected aggregate analysis JSON files.
Copied from the archived generator; the frozen original is never modified. It is
styled to match Figures 1-3:
grayscale value tiers, square heavy borders, bold sans headings, one blue
accent reserved for the context-engineering-side outputs, and the dashed
callout card used for special notices (as in Figure 2's Metadata Paradox).
Authored at 190 mm; placed at \\linewidth (390 pt) the 10 pt floor renders at
7.24 pt.
"""
import argparse
import json
import os
from pathlib import Path

from ce_figstyle import (
    FIG_W_IN, FS_TITLE, FS_HEAD, FS_SEC, FS_MIN, INK, MUTED, EDGE,
    LIGHT, MID, PALE, ACCENT, ACCENT_EDGE, LW_BOX, arrow, card, label,
    new_canvas, pt2x, pt2y, rule, save, wrap_pt,
)

HERE = os.path.dirname(os.path.abspath(__file__))

parser = argparse.ArgumentParser()
parser.add_argument("--analysis-summary", required=True, type=Path)
parser.add_argument("--inheritance-summary", required=True, type=Path)
parser.add_argument("--output-dir", type=Path, default=Path(HERE))
args = parser.parse_args()
summary = json.loads(args.analysis_summary.read_text(encoding="utf-8"))
inheritance = json.loads(args.inheritance_summary.read_text(encoding="utf-8"))
scope = summary["scope"]
pilot = inheritance["scope"]
candidate_positive = pilot["high_confidence_candidates"] + pilot["probable_candidates"]
candidate_rate = 100 * candidate_positive / pilot["eligible_rows_with_prior_action_eligible_ce"]

H = 4.55
fig, ax = new_canvas(H)
W_PT = FIG_W_IN * 72.0


def wrap(s, size, max_pt, weight="normal", style="normal"):
    return wrap_pt(fig, s, size, max_pt, weight, style)


def flowcard(x, w, y, h, title, lines, *, fill=LIGHT, edge=EDGE, lw=LW_BOX):
    card(ax, x, y, w, h, fill=fill, edge=edge, lw=lw)
    inner = w * FIG_W_IN * 72.0 - 14
    assert wrap_pt(fig, title, FS_SEC, weight="bold") if False else True
    tw = wrap(title, FS_SEC, inner, "bold")
    assert "\n" not in tw, f"title wraps: {title!r}"
    label(ax, x + w / 2, y + h - pt2y(ax, 12), tw, size=FS_SEC, weight="bold",
          ha="center", va="center")
    rule(ax, x + pt2x(8), x + w - pt2x(8), y + h - pt2y(ax, 19))
    ly = y + h - pt2y(ax, 26)
    for ln in lines:
        wl = wrap(ln, FS_MIN, inner)
        k = wl.count("\n") + 1
        label(ax, x + w / 2, ly, wl, size=FS_MIN, color="#3f3f3f",
              ha="center", va="top", linespacing=1.22)
        ly -= pt2y(ax, 13.2) * k


label(ax, 0.5, 0.965, "ANALYSIS CONSTRUCTION AND INTERPRETATION BOUNDARY",
      size=FS_TITLE, weight="bold", ha="center")
label(ax, 0.5, 0.928,
      "balanced cohorts and a separate candidate-linkage pilot; every label is automated and unadjudicated",
      size=FS_SEC, style="italic", color=MUTED, ha="center")

MARG = 0.020
GAP = pt2x(16)

# ===========================================================================
# Band A - balanced construction (four cards, left to right)
# ===========================================================================
label(ax, MARG, 0.868, "A   Balanced construction  (13-archive source frame)",
      size=FS_HEAD, weight="bold", va="center")

cw = (1 - 2 * MARG - 3 * GAP) / 4
ch = pt2y(ax, 78)
cy = 0.868 - pt2y(ax, 14) - ch
CARDS_A = [
    ("Normalized frame",
     ['31,919 source segments',
      f'→ {scope["source_episode_rows"]:,} trajectories',
      f'{scope["source_station_archives"]} station archives'], MID, EDGE, LW_BOX),
    ("Action-eligible pools",
     [f'ordered candidates: {scope["action_eligible_ce_candidates"]:,}',
      f'frontloaded: {scope["action_eligible_frontloaded_ce_candidates"]:,}',
      f'comparison: {scope["action_eligible_routed_comparisons"]:,}'], LIGHT, EDGE, LW_BOX),
    ("Stratum balance",
     ["station·provider·month",
      f'primary {scope["primary_frontloaded_balanced_per_condition"]:,}/cond.',
      f'unrestr. {scope["unrestricted_balanced_per_condition"]:,}/cond.'], PALE, EDGE, LW_BOX),
    ("Outputs",
     ["six process signals", "action/timing measures", "station sensitivities"], ACCENT, ACCENT_EDGE, 1.9),
]
for i, (t, lines, fill, edge, lw) in enumerate(CARDS_A):
    x = MARG + i * (cw + GAP)
    flowcard(x, cw, cy, ch, t, lines, fill=fill, edge=edge, lw=lw)
    if i < 3:
        arrow(ax, (x + cw, cy + ch / 2), (x + cw + GAP, cy + ch / 2),
              lw=1.6, scale=12)

# ===========================================================================
# Band B - separate pilot (three cards)
# ===========================================================================
by_head = cy - pt2y(ax, 22)
label(ax, MARG, by_head, "B   Separate inherited-context candidate-linkage pilot  (three-station scope)",
      size=FS_HEAD, weight="bold", va="center")

bw = (1 - 2 * MARG - 2 * GAP) / 3
bh = pt2y(ax, 64)
by = by_head - pt2y(ax, 14) - bh
CARDS_B = [
    ("Comparison rows", [f'{pilot["action_eligible_comparison_rows_mapped"]:,} action-eligible',
                         "routed-comparison rows"], LIGHT),
    ("Eligible linkage set", [f'{pilot["eligible_rows_with_prior_action_eligible_ce"]:,} eligible; prior candidate',
                              f'strong or probable; {pilot["clean_origin_candidates"]:,} none'], LIGHT),
    ("Candidate linkage", [f'{candidate_positive:,} candidate-positive ({candidate_rate:.1f}%)',
                           f'{pilot["unresolved_primary_rule"]:,} unresolved'], PALE),
]
for i, (t, lines, fill) in enumerate(CARDS_B):
    x = MARG + i * (bw + GAP)
    flowcard(x, bw, by, bh, t, lines, fill=fill)
    if i < 2:
        arrow(ax, (x + bw, by + bh / 2), (x + bw + GAP, by + bh / 2),
              lw=1.6, scale=12)

# ===========================================================================
# Interpretation boundary - dashed callout, as in Figure 2's paradox card
# ===========================================================================
ib_h = pt2y(ax, 46)
ib_y = by - pt2y(ax, 20) - ib_h
card(ax, MARG, ib_y, 1 - 2 * MARG, ib_h, fill=PALE, edge="#7d7d7d",
     lw=1.3, ls=(0, (5, 3)))
label(ax, 0.5, ib_y + ib_h - pt2y(ax, 13), "INTERPRETATION BOUNDARY",
      size=FS_SEC, weight="bold", color="#2b2b2b", ha="center")
label(ax, 0.5, ib_y + pt2y(ax, 13),
      wrap("Automated, classifier-coupled process proxies; no causal, product-quality, "
           "participant-level, confirmed-inheritance, or directional speed claim.",
           FS_MIN, (1 - 2 * MARG) * W_PT - 20),
      size=FS_MIN, color=MUTED, ha="center", va="center", linespacing=1.3)

# key for the single accent
label(ax, MARG, ib_y - pt2y(ax, 13),
      "Native identity and primary boundaries are reconciled; archives are not independent people or tasks.",
      size=FS_MIN, style="italic", color=MUTED)

args.output_dir.mkdir(parents=True, exist_ok=True)
pdf = args.output_dir / "fig-06-analysis-evidence-map.pdf"
fig.savefig(pdf, facecolor="white")
print(f"wrote {pdf.name}")
