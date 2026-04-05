#!/usr/bin/env python3
"""
gen_briefing.py — BWSI AUVC pre-mission briefing generator
===========================================================

Reads any BWSI scenario TOML file and produces:
  1. A PNG/PDF mission briefing figure  (if matplotlib is available)
  2. A text summary printed to stdout   (always)

Auto-detects scenario type from TOML contents:
  game       — has [[npcs]]
  inspection — has [[pipelines]]
  gps_denied — has [[beacons]]

Usage:
    python briefing/gen_briefing.py --scenario missions/game/scenarios/scavenger_hunt.toml
    python briefing/gen_briefing.py --scenario missions/inspection/scenarios/pipeline_survey.toml
    python briefing/gen_briefing.py --scenario missions/gps_denied/scenarios/beacon_nav.toml
    python briefing/gen_briefing.py --scenario ... --output /tmp/brief.png --no-show
"""

from __future__ import annotations

import argparse
import math
import os
import sys
from textwrap import dedent
from typing import List, Tuple

try:
    import tomllib
except ImportError:
    try:
        import tomli as tomllib
    except ImportError:
        print("ERROR: TOML library not found.  pip install tomli  (Python < 3.11)")
        sys.exit(1)

try:
    import matplotlib
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    import matplotlib.patheffects as pe
    from matplotlib.lines import Line2D
    from matplotlib.patches import FancyArrow, Polygon, FancyArrowPatch
    from matplotlib.collections import LineCollection
    HAS_MPL = True
except ImportError:
    HAS_MPL = False


# ---------------------------------------------------------------------------
# Colour palette
# ---------------------------------------------------------------------------
TEAM_COLORS = {
    "dodger_blue": "#1E90FF",
    "orange":      "#FF8C00",
    "red":         "#DC143C",
    "green":       "#228B22",
    "purple":      "#8B008B",
    "cyan":        "#00CED1",
}

NPC_COLORS = {
    "shark":    "#FF4444",
    "fish":     "#00CED1",
    "whale":    "#AAAAAA",
    "treasure": "#FFD700",
}

PIPELINE_COLOR  = "#FFD700"
BEACON_COLOR    = "#4FC3F7"
ANOMALY_COLOR   = "#FF6B35"
SEARCH_COLOR    = "#80CBC4"
ARENA_COLOR     = "#EF5350"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def resolve_color(c: str) -> str:
    return TEAM_COLORS.get(c, c)


def poly_to_xy(vertices: list) -> Tuple[List[float], List[float]]:
    xs = [v[0] for v in vertices] + [vertices[0][0]]
    ys = [v[1] for v in vertices] + [vertices[0][1]]
    return xs, ys


def heading_arrow(ax, x, y, hdg_deg, length=12, color="white"):
    """Draw a short arrow in the heading direction."""
    rad = math.radians(90 - hdg_deg)   # MOOS: 0=north, clockwise
    dx  = length * math.cos(rad)
    dy  = length * math.sin(rad)
    ax.annotate("", xy=(x + dx, y + dy), xytext=(x, y),
                arrowprops=dict(arrowstyle="-|>", color=color, lw=1.5))


def detect_scenario_type(cfg: dict) -> str:
    if "pipelines" in cfg:
        return "inspection"
    if "beacons" in cfg:
        return "gps_denied"
    if "npcs" in cfg:
        return "game"
    return "unknown"


# ---------------------------------------------------------------------------
# Text summary (always printed, regardless of matplotlib)
# ---------------------------------------------------------------------------

def print_text_briefing(cfg: dict, stype: str):
    sc     = cfg.get("scenario", {})
    teams  = cfg.get("teams", [])
    origin = cfg.get("origin", {})

    n_vehicles = sum(len(t.get("vehicles", [])) for t in teams)

    sep = "=" * 64

    print(sep)
    print(f"  BWSI AUVC  ·  {sc.get('name', 'Mission').upper()}")
    print(f"  Type: {stype.replace('_', ' ').title()}")
    print(sep)
    print(f"  {sc.get('description', '')}")
    print()

    # Scoring
    scoring = cfg.get("scoring", cfg.get("game", {}))
    if scoring:
        print("  SCORING")
        print("  " + "-" * 30)
        for k, v in scoring.items():
            if k != "length_min":
                label = k.replace("_", " ").capitalize()
                print(f"    {label:<28} {v}")
        dur = scoring.get("length_min", sc.get("length_min", "?"))
        print(f"    {'Duration (min)':<28} {dur}")
        print()

    # Teams
    print("  TEAMS")
    print("  " + "-" * 30)
    for t in teams:
        for v in t.get("vehicles", []):
            mode = v.get("student_mode", "cpp").upper()
            print(f"    [{t['name'].upper():6s}] {v['name']:<12} "
                  f"start=({v.get('start_x',0):.0f},{v.get('start_y',0):.0f})  "
                  f"mode={mode}")
    print()

    # Scenario-specific
    if stype == "inspection":
        pipes = cfg.get("pipelines", [])
        anoms = cfg.get("anomalies", [])
        sensor = cfg.get("sensor", {})
        print("  INFRASTRUCTURE")
        print("  " + "-" * 30)
        for p in pipes:
            print(f"    Pipeline '{p['label']}': depth={p['depth']}m, "
                  f"{len(p['points'])} waypoints")
        print(f"    Anomalies to find: {len(anoms)}")
        print(f"    Sensor range: {sensor.get('detect_range', 30)}m  "
              f"cone: ±{sensor.get('detect_cone', 60)}°  "
              f"noise: {sensor.get('noise_sigma', 3)}m σ")
        print()

    elif stype == "gps_denied":
        beacons = cfg.get("beacons", [])
        dive    = cfg.get("dive", {})
        acoustic = cfg.get("acoustic", {})
        print("  ACOUSTIC NAVIGATION")
        print("  " + "-" * 30)
        for b in beacons:
            print(f"    {b['label']}: ({b['x']:.0f}, {b['y']:.0f})")
        print(f"    Search depth:    {dive.get('search_depth', 15)}m")
        print(f"    Surface period:  every {dive.get('surface_period', 60)}s")
        print(f"    Range noise:     ±{acoustic.get('noise_magnitude', 2)}m")
        print()

    elif stype == "game":
        npcs = cfg.get("npcs", [])
        game = cfg.get("game", {})
        print("  NPC ENTITIES")
        print("  " + "-" * 30)
        for npc in npcs:
            print(f"    {npc['type'].upper():<10} '{npc['name']}'  "
                  f"start=({npc.get('start_x',0):.0f},{npc.get('start_y',0):.0f})")
        print()

    # Origin
    print(f"  Origin: {origin.get('lat','?')}°N, {origin.get('lon','?')}°E")
    print(sep)


# ---------------------------------------------------------------------------
# Figure layout
# ---------------------------------------------------------------------------

def make_figure(cfg: dict, stype: str, output_path: str, show: bool):
    fig = plt.figure(figsize=(16, 10), facecolor="#1A1A2E")
    fig.patch.set_facecolor("#1A1A2E")

    # Two columns: map (left, 60%) and info panel (right, 40%)
    gs = fig.add_gridspec(1, 2, width_ratios=[6, 4],
                          left=0.04, right=0.97,
                          top=0.88, bottom=0.06,
                          wspace=0.06)
    ax_map  = fig.add_subplot(gs[0])
    ax_info = fig.add_subplot(gs[1])

    sc = cfg.get("scenario", {})

    # ---- Title bar ----
    stype_label = {"game": "Game Challenge",
                   "inspection": "Infrastructure Inspection",
                   "gps_denied": "GPS-Denied Navigation"}.get(stype, "Mission")
    fig.text(0.5, 0.95, sc.get("name", "Mission Brief").upper(),
             ha="center", va="center", fontsize=20, color="white", fontweight="bold")
    fig.text(0.5, 0.915, f"BWSI AUVC  ·  {stype_label}",
             ha="center", va="center", fontsize=12, color="#90CAF9")

    draw_map(ax_map, cfg, stype)
    draw_info_panel(ax_info, cfg, stype)

    if output_path:
        fig.savefig(output_path, dpi=150, bbox_inches="tight",
                    facecolor=fig.get_facecolor())
        print(f"  Briefing saved to: {output_path}")

    if show:
        plt.show()
    else:
        plt.close(fig)


# ---------------------------------------------------------------------------
# Map panel
# ---------------------------------------------------------------------------

BG_MAP  = "#0D1B2A"
GRID_C  = "#1E3A5F"
TEXT_C  = "#E0E0E0"


def draw_map(ax, cfg, stype):
    ax.set_facecolor(BG_MAP)
    ax.tick_params(colors=TEXT_C, labelsize=8)
    for spine in ax.spines.values():
        spine.set_edgecolor("#2A4A6A")

    arena_v = cfg["arena"]["vertices"]
    ax_xs, ax_ys = poly_to_xy(arena_v)

    # Compute bounds with margin
    all_x = ax_xs; all_y = ax_ys
    margin_x = (max(all_x) - min(all_x)) * 0.08
    margin_y = (max(all_y) - min(all_y)) * 0.08
    ax.set_xlim(min(all_x) - margin_x, max(all_x) + margin_x)
    ax.set_ylim(min(all_y) - margin_y, max(all_y) + margin_y)
    ax.set_aspect("equal")
    ax.grid(True, color=GRID_C, linewidth=0.5, linestyle="--", alpha=0.6)
    ax.set_xlabel("X (m east of origin)", color=TEXT_C, fontsize=9)
    ax.set_ylabel("Y (m north of origin)", color=TEXT_C, fontsize=9)
    ax.tick_params(axis="both", colors=TEXT_C)

    # Arena boundary
    ax.plot(ax_xs, ax_ys, color=ARENA_COLOR, linewidth=2,
            linestyle="--", label="Arena boundary")
    ax.fill(ax_xs[:-1], ax_ys[:-1], color=ARENA_COLOR, alpha=0.04)

    legend_handles = [
        Line2D([0], [0], color=ARENA_COLOR, linewidth=2, linestyle="--",
               label="Arena boundary"),
    ]

    if stype == "game":
        legend_handles += draw_game_features(ax, cfg)
    elif stype == "inspection":
        legend_handles += draw_inspection_features(ax, cfg)
    elif stype == "gps_denied":
        legend_handles += draw_gps_denied_features(ax, cfg)

    legend_handles += draw_vehicles(ax, cfg)
    draw_north_arrow(ax)
    draw_scale_bar(ax, arena_v)

    ax.legend(handles=legend_handles, loc="upper right",
              facecolor="#0D1B2A", edgecolor="#2A4A6A",
              labelcolor=TEXT_C, fontsize=8, framealpha=0.9)


def draw_game_features(ax, cfg) -> list:
    handles = []
    npcs = cfg.get("npcs", [])

    for npc in npcs:
        ntype = npc["type"]
        color = NPC_COLORS.get(ntype, "#FFFFFF")
        sx, sy = npc.get("start_x", 0), npc.get("start_y", 0)

        # Patrol polygon
        patrol_str = npc.get("patrol_polygon", "")
        if patrol_str:
            pts = [tuple(map(float, seg.split(",")))
                   for seg in patrol_str.split(":")]
            xs, ys = poly_to_xy(pts)
            ax.plot(xs, ys, color=color, linewidth=1,
                    linestyle=":", alpha=0.6)
            ax.fill(xs[:-1], ys[:-1], color=color, alpha=0.06)

        # NPC marker
        marker_map = {"shark": "^", "fish": "D",
                      "whale": "s", "treasure": "*"}
        m = marker_map.get(ntype, "o")
        ax.scatter(sx, sy, c=color, s=120, marker=m,
                   zorder=5, edgecolors="white", linewidths=0.8)
        ax.annotate(npc["name"], (sx, sy), textcoords="offset points",
                    xytext=(6, 6), fontsize=7, color=color)

    # Legend entries per NPC type seen
    seen_types = set()
    for npc in npcs:
        t = npc["type"]
        if t not in seen_types:
            seen_types.add(t)
            handles.append(Line2D([0], [0],
                marker={"shark":"^","fish":"D","whale":"s","treasure":"*"}.get(t,"o"),
                color="w", markerfacecolor=NPC_COLORS.get(t,"w"),
                markersize=8, label=f"NPC: {t}"))
    return handles


def draw_inspection_features(ax, cfg) -> list:
    handles = []
    pipes = cfg.get("pipelines", [])
    anoms = cfg.get("anomalies", [])

    for pipe in pipes:
        pts = pipe["points"]
        xs  = [p[0] for p in pts]
        ys  = [p[1] for p in pts]

        # Pipeline route
        ax.plot(xs, ys, color=PIPELINE_COLOR, linewidth=3,
                solid_capstyle="round", zorder=4, label=pipe["label"])
        ax.scatter(xs, ys, c=PIPELINE_COLOR, s=40, zorder=5)

        # Sensor corridor band (±detect_range around each segment)
        sensor_range = cfg.get("sensor", {}).get("detect_range", 30)
        for i in range(len(pts) - 1):
            x1, y1 = pts[i];   x2, y2 = pts[i+1]
            dx, dy = x2-x1, y2-y1
            L = math.sqrt(dx*dx + dy*dy)
            if L < 1e-6: continue
            nx, ny = -dy/L*sensor_range, dx/L*sensor_range
            corridor = [(x1+nx, y1+ny), (x2+nx, y2+ny),
                        (x2-nx, y2-ny), (x1-nx, y1-ny)]
            ax.fill([p[0] for p in corridor],
                    [p[1] for p in corridor],
                    color=PIPELINE_COLOR, alpha=0.08)

        handles.append(Line2D([0], [0], color=PIPELINE_COLOR, linewidth=3,
                               label=f"Pipeline: {pipe['label']}"))

    # Anomaly markers — shown as "?" since position is uncertain
    for i, anom in enumerate(anoms):
        ax.scatter(anom["x"], anom["y"], c=ANOMALY_COLOR,
                   s=180, marker="D", zorder=6,
                   edgecolors="white", linewidths=1.2)
        ax.annotate(f"?  {anom['type']}", (anom["x"], anom["y"]),
                    textcoords="offset points", xytext=(8, 6),
                    fontsize=7, color=ANOMALY_COLOR,
                    fontweight="bold")

    if anoms:
        handles.append(Line2D([0], [0], marker="D", color="w",
                               markerfacecolor=ANOMALY_COLOR, markersize=9,
                               label="Anomaly (position unknown)"))
    return handles


def draw_gps_denied_features(ax, cfg) -> list:
    handles = []
    beacons = cfg.get("beacons", [])
    acoustic = cfg.get("acoustic", {})
    push_dist = acoustic.get("push_dist", 120.0)

    # Search box
    sb_v = cfg.get("search_box", {}).get("vertices", [])
    if sb_v:
        xs, ys = poly_to_xy(sb_v)
        ax.plot(xs, ys, color=SEARCH_COLOR, linewidth=2,
                linestyle="-.", label="Search box")
        ax.fill(xs[:-1], ys[:-1], color=SEARCH_COLOR, alpha=0.08)
        cx = sum(v[0] for v in sb_v) / len(sb_v)
        cy = sum(v[1] for v in sb_v) / len(sb_v)
        ax.text(cx, cy, "SEARCH\nAREA", ha="center", va="center",
                color=SEARCH_COLOR, fontsize=9, fontweight="bold", alpha=0.7)
        handles.append(Line2D([0], [0], color=SEARCH_COLOR, linewidth=2,
                               linestyle="-.", label="Search box"))

    # Beacons with range circles
    for b in beacons:
        bx, by = b["x"], b["y"]
        circle = plt.Circle((bx, by), push_dist, color=BEACON_COLOR,
                             fill=False, linewidth=1, linestyle=":",
                             alpha=0.4)
        ax.add_patch(circle)
        ax.scatter(bx, by, c=BEACON_COLOR, s=150, marker="^",
                   zorder=6, edgecolors="white", linewidths=1)
        ax.annotate(b["label"], (bx, by), textcoords="offset points",
                    xytext=(6, 6), fontsize=7, color=BEACON_COLOR)

    if beacons:
        handles.append(Line2D([0], [0], marker="^", color="w",
                               markerfacecolor=BEACON_COLOR, markersize=9,
                               label=f"Acoustic beacon (r={push_dist:.0f}m)"))
    return handles


def draw_vehicles(ax, cfg) -> list:
    teams = cfg.get("teams", [])
    handles = []
    for team in teams:
        color = resolve_color(team.get("color", "white"))
        for v in team.get("vehicles", []):
            sx, sy = v.get("start_x", 0), v.get("start_y", 0)
            hdg    = v.get("start_heading", 0)
            ax.scatter(sx, sy, c=color, s=200, marker="o",
                       zorder=7, edgecolors="white", linewidths=1.5)
            heading_arrow(ax, sx, sy, hdg, length=18, color=color)
            ax.annotate(f"{team['name']}\n{v['name']}",
                        (sx, sy), textcoords="offset points",
                        xytext=(-10, -22), fontsize=7, color=color,
                        ha="center")
        handles.append(Line2D([0], [0], marker="o", color="w",
                               markerfacecolor=color, markersize=9,
                               label=f"Team {team['name']}"))
    return handles


def draw_north_arrow(ax):
    """Small north arrow in the upper-left corner of the map."""
    xlim = ax.get_xlim(); ylim = ax.get_ylim()
    x0 = xlim[0] + 0.05 * (xlim[1] - xlim[0])
    y0 = ylim[0] + 0.10 * (ylim[1] - ylim[0])
    dy = 0.06 * (ylim[1] - ylim[0])
    ax.annotate("", xy=(x0, y0+dy), xytext=(x0, y0),
                arrowprops=dict(arrowstyle="-|>", color=TEXT_C, lw=1.5))
    ax.text(x0, y0 + dy + 0.005*(ylim[1]-ylim[0]),
            "N", ha="center", va="bottom", color=TEXT_C,
            fontsize=9, fontweight="bold")


def draw_scale_bar(ax, arena_vertices):
    """Simple scale bar in the lower-left corner."""
    xlim = ax.get_xlim(); ylim = ax.get_ylim()
    x0 = xlim[0] + 0.05 * (xlim[1] - xlim[0])
    y0 = ylim[0] + 0.03 * (ylim[1] - ylim[0])

    arena_w = max(v[0] for v in arena_vertices) - min(v[0] for v in arena_vertices)
    # Pick a round number: ~20% of arena width
    bar_m = round(arena_w * 0.2 / 50) * 50
    bar_m = max(50, bar_m)

    ax.plot([x0, x0 + bar_m], [y0, y0], color=TEXT_C, linewidth=2)
    ax.plot([x0, x0], [y0 - 3, y0 + 3], color=TEXT_C, linewidth=2)
    ax.plot([x0+bar_m, x0+bar_m], [y0-3, y0+3], color=TEXT_C, linewidth=2)
    ax.text(x0 + bar_m/2, y0 + 6, f"{bar_m} m",
            ha="center", va="bottom", color=TEXT_C, fontsize=7)


# ---------------------------------------------------------------------------
# Info panel
# ---------------------------------------------------------------------------

INFO_BG  = "#0F2033"
HEADING_C = "#90CAF9"
VALUE_C   = "#E0E0E0"
DIM_C     = "#607D8B"


def draw_info_panel(ax, cfg, stype):
    ax.set_facecolor(INFO_BG)
    ax.axis("off")
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)

    sc      = cfg.get("scenario", {})
    teams   = cfg.get("teams", [])
    scoring = cfg.get("scoring", cfg.get("game", {}))

    y = 0.97
    dy_heading = 0.045
    dy_line    = 0.033
    dy_small   = 0.026

    def heading(text, ypos):
        ax.text(0.05, ypos, text, transform=ax.transAxes,
                fontsize=10, fontweight="bold", color=HEADING_C, va="top")
        ax.axhline(y=ypos - 0.012, xmin=0.04, xmax=0.96,
                   color=HEADING_C, linewidth=0.8, alpha=0.5,
                   transform=ax.transAxes)
        return ypos - dy_heading

    def kv(key, value, ypos, indent=0.07):
        ax.text(indent, ypos, key + ":", transform=ax.transAxes,
                fontsize=8.5, color=DIM_C, va="top")
        ax.text(0.55, ypos, str(value), transform=ax.transAxes,
                fontsize=8.5, color=VALUE_C, va="top")
        return ypos - dy_line

    def line(text, ypos, indent=0.07, color=VALUE_C, size=8.5):
        ax.text(indent, ypos, text, transform=ax.transAxes,
                fontsize=size, color=color, va="top")
        return ypos - dy_small

    # Mission description
    ax.text(0.05, y, sc.get("description", ""), transform=ax.transAxes,
            fontsize=8, color=DIM_C, va="top", wrap=True,
            style="italic")
    y -= 0.055

    # Duration
    dur = scoring.get("length_min", sc.get("length_min", "?"))
    y = heading("MISSION PARAMETERS", y)
    y = kv("Duration", f"{dur} min", y)
    y = kv("Teams", len(teams), y)
    n_veh = sum(len(t.get("vehicles",[])) for t in teams)
    y = kv("Vehicles", n_veh, y)
    y -= 0.01

    # Teams
    y = heading("TEAMS", y)
    for t in teams:
        tcolor = resolve_color(t.get("color", "white"))
        for v in t.get("vehicles", []):
            mode = v.get("student_mode", "cpp").upper()
            txt  = f"  ■  [{t['name'].upper()}] {v['name']}  ({mode})"
            ax.text(0.05, y, txt, transform=ax.transAxes,
                    fontsize=8.5, color=tcolor, va="top")
            y -= dy_small
    y -= 0.01

    # Scoring
    y = heading("SCORING", y)
    skip_keys = {"length_min"}
    for k, v_val in scoring.items():
        if k in skip_keys: continue
        y = kv(k.replace("_", " ").capitalize(), v_val, y)
    y -= 0.01

    # Type-specific info
    if stype == "inspection":
        y = _info_inspection(ax, cfg, y, heading, kv, line)
    elif stype == "gps_denied":
        y = _info_gps_denied(ax, cfg, y, heading, kv, line)
    elif stype == "game":
        y = _info_game(ax, cfg, y, heading, kv, line)

    # Objectives at bottom
    y = max(y, 0.22)
    y = heading("OBJECTIVES", y)
    objs = _objectives(cfg, stype)
    for obj in objs:
        y = line(f"  ◆  {obj}", y, color="#A5D6A7")


def _info_inspection(ax, cfg, y, heading, kv, line):
    pipes  = cfg.get("pipelines", [])
    anoms  = cfg.get("anomalies", [])
    sensor = cfg.get("sensor", {})
    y = heading("INFRASTRUCTURE", y)
    for p in pipes:
        y = kv(f"Pipeline '{p['label']}'",
                f"depth {p['depth']}m, {len(p['points'])} pts", y)
    y = kv("Anomalies", f"{len(anoms)} (positions hidden)", y)
    y -= 0.01
    y = heading("SENSOR MODEL", y)
    y = kv("Detect range", f"{sensor.get('detect_range', 30)} m", y)
    y = kv("Detect cone", f"±{sensor.get('detect_cone', 60)}°", y)
    y = kv("Position noise", f"{sensor.get('noise_sigma', 3)} m σ", y)
    y = kv("False alarm rate",
           f"{sensor.get('p_false_alarm', 0.02):.2f} / veh / s", y)
    return y


def _info_gps_denied(ax, cfg, y, heading, kv, line):
    beacons  = cfg.get("beacons", [])
    dive     = cfg.get("dive", {})
    acoustic = cfg.get("acoustic", {})
    y = heading("ACOUSTIC BEACONS", y)
    for b in beacons:
        y = kv(b["label"], f"({b['x']:.0f}, {b['y']:.0f})", y)
    y = kv("Push distance", f"{acoustic.get('push_dist', 120)} m", y)
    y = kv("Range noise",   f"±{acoustic.get('noise_magnitude', 2)} m", y)
    y -= 0.01
    y = heading("DIVE PROFILE", y)
    y = kv("Search depth",   f"{dive.get('search_depth', 15)} m", y)
    y = kv("Surface period", f"every {dive.get('surface_period', 60)} s", y)
    y = kv("At surface for", f"{dive.get('surface_time', 20)} s", y)
    return y


def _info_game(ax, cfg, y, heading, kv, line):
    npcs = cfg.get("npcs", [])
    game = cfg.get("game", {})
    y = heading("NPC ENTITIES", y)
    for npc in npcs:
        y = kv(f"  {npc['type'].upper()} '{npc['name']}'",
               f"speed {npc.get('patrol_speed', 1.5)} m/s", y)
    return y


def _objectives(cfg, stype) -> list:
    if stype == "game":
        game = cfg.get("game", {})
        return [
            f"Tag whales (+{game.get('whale_score', 300)} pts each)",
            f"Photograph fish (+{game.get('fish_score', 100)} pts each)",
            f"Collect treasure (+{game.get('collect_score', 500)} pts)",
            "Avoid sharks (bite = penalty box timeout)",
        ]
    elif stype == "inspection":
        scoring = cfg.get("scoring", {})
        return [
            "Survey the full cable corridor",
            f"Locate {len(cfg.get('anomalies',[]))} anomalies along the cable",
            f"Report anomaly positions to shoreside",
            "Minimise false-alarm reports",
        ]
    elif stype == "gps_denied":
        scoring = cfg.get("scoring", {})
        return [
            "Cover the designated search box",
            "Navigate using acoustic beacon ranges",
            "Surface periodically to acquire GPS fix",
            "Minimise navigation error at surface",
        ]
    return []


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Generate a pre-mission briefing from a BWSI scenario TOML")
    parser.add_argument("--scenario", required=True,
                        help="Path to scenario TOML file")
    parser.add_argument("--output", default=None,
                        help="Output image path (default: <outdir>/briefing.png)")
    parser.add_argument("--no-show", action="store_true",
                        help="Do not open the figure interactively")
    parser.add_argument("--text-only", action="store_true",
                        help="Only print text summary; skip matplotlib")
    args = parser.parse_args()

    with open(args.scenario, "rb") as f:
        cfg = tomllib.load(f)

    stype = detect_scenario_type(cfg)
    print_text_briefing(cfg, stype)

    if args.text_only:
        return

    if not HAS_MPL:
        print("\nNote: matplotlib not installed — skipping graphic output.")
        print("  pip install matplotlib  to enable mission briefing graphics.")
        return

    output = args.output
    if output is None:
        scenario_dir = os.path.dirname(os.path.abspath(args.scenario))
        output = os.path.join(scenario_dir, "..", "run",
                              os.path.splitext(
                                  os.path.basename(args.scenario))[0],
                              "briefing.png")
        output = os.path.abspath(output)

    os.makedirs(os.path.dirname(output), exist_ok=True)
    make_figure(cfg, stype, output, show=not args.no_show)


if __name__ == "__main__":
    main()
