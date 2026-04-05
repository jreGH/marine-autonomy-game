#!/usr/bin/env python3
"""
post_visuals.py — inject static mission visuals into the live pMarineViewer
============================================================================

Connects to the shoreside MOOSDB and publishes VIEW_SEGLIST / VIEW_POINT
messages so the mission map is pre-populated before vehicles start moving.

Run this AFTER the shoreside community starts:
    python briefing/post_visuals.py --scenario missions/inspection/scenarios/pipeline_survey.toml
    python briefing/post_visuals.py --scenario missions/gps_denied/scenarios/beacon_nav.toml
    python briefing/post_visuals.py --scenario missions/game/scenarios/scavenger_hunt.toml

Optional arguments:
    --port  PORT   Shoreside MOOSDB port (default: 9100)
    --host  HOST   MOOSDB hostname (default: localhost)
"""

from __future__ import annotations

import argparse
import math
import sys
import time

try:
    import tomllib
except ImportError:
    try:
        import tomli as tomllib
    except ImportError:
        print("ERROR: TOML library not found.")
        sys.exit(1)

try:
    import pymoos
    HAS_PYMOOS = True
except ImportError:
    HAS_PYMOOS = False


# ---------------------------------------------------------------------------
# VIEW_* message builders
# ---------------------------------------------------------------------------

def view_seglist(points: list, label: str, color: str = "yellow",
                 edge_size: int = 2) -> str:
    pts = ":".join(f"{p[0]:.1f},{p[1]:.1f}" for p in points)
    return (f"pts={pts},label={label},"
            f"edge_color={color},edge_size={edge_size},"
            f"vertex_color={color},vertex_size=4")


def view_polygon(vertices: list, label: str, color: str,
                 alpha: float = 0.1) -> str:
    pts = ":".join(f"{v[0]:.1f},{v[1]:.1f}" for v in vertices)
    return (f"pts={pts},label={label},"
            f"edge_color={color},edge_size=1,"
            f"vertex_color={color},vertex_size=3")


def view_point(x: float, y: float, label: str, color: str,
               size: int = 6, shape: str = "circle") -> str:
    return (f"x={x:.1f},y={y:.1f},label={label},"
            f"color={color},vertex_size={size},"
            f"vertex_style={shape}")


def view_circle(cx: float, cy: float, radius: float,
                label: str, color: str) -> str:
    """Approximate a circle as a VIEW_SEGLIST polygon (32-gon)."""
    n = 32
    pts = [(cx + radius * math.cos(2*math.pi*i/n),
            cy + radius * math.sin(2*math.pi*i/n))
           for i in range(n)]
    return view_seglist(pts + [pts[0]], label, color=color, edge_size=1)


# ---------------------------------------------------------------------------
# Per-scenario visual generators
# ---------------------------------------------------------------------------

def game_visuals(cfg: dict) -> list:
    """Return [(var, val), …] VIEW messages for a game scenario."""
    msgs = []
    arena_v = cfg["arena"]["vertices"]
    msgs.append(("VIEW_SEGLIST",
                  view_polygon(arena_v, "arena", color="red")))

    for npc in cfg.get("npcs", []):
        pstr = npc.get("patrol_polygon", "")
        if pstr:
            pts = [tuple(map(float, s.split(","))) for s in pstr.split(":")]
            ntype = npc["type"]
            cmap  = {"shark":"red","fish":"cyan","whale":"white","treasure":"gold"}
            color = cmap.get(ntype, "white")
            msgs.append(("VIEW_SEGLIST",
                          view_polygon(pts, f"patrol_{npc['name']}", color=color)))
        msgs.append(("VIEW_POINT",
                      view_point(npc["start_x"], npc["start_y"],
                                 label=npc["name"],
                                 color={"shark":"red","fish":"cyan",
                                        "whale":"white","treasure":"gold"}.get(
                                             npc["type"], "white"),
                                 size=8, shape="triangle")))
    return msgs


def inspection_visuals(cfg: dict) -> list:
    msgs = []
    msgs.append(("VIEW_SEGLIST",
                  view_polygon(cfg["arena"]["vertices"], "arena", color="red")))

    for pipe in cfg.get("pipelines", []):
        msgs.append(("VIEW_SEGLIST",
                      view_seglist(pipe["points"], label=pipe["label"],
                                   color="yellow", edge_size=3)))

    # Anomalies shown as question marks (label only — position revealed on discovery)
    for i, anom in enumerate(cfg.get("anomalies", [])):
        msgs.append(("VIEW_POINT",
                      view_point(anom["x"], anom["y"],
                                 label=f"anomaly_{i}_{anom['type']}",
                                 color="orange", size=8, shape="diamond")))
    return msgs


def gps_denied_visuals(cfg: dict) -> list:
    msgs = []
    msgs.append(("VIEW_SEGLIST",
                  view_polygon(cfg["arena"]["vertices"], "arena", color="red")))

    sb_v = cfg.get("search_box", {}).get("vertices", [])
    if sb_v:
        msgs.append(("VIEW_SEGLIST",
                      view_polygon(sb_v, "search_box", color="cyan")))

    push_dist = cfg.get("acoustic", {}).get("push_dist", 120.0)
    for b in cfg.get("beacons", []):
        msgs.append(("VIEW_POINT",
                      view_point(b["x"], b["y"], label=b["label"],
                                 color="blue", size=8, shape="triangle")))
        msgs.append(("VIEW_SEGLIST",
                      view_circle(b["x"], b["y"], push_dist,
                                  label=f"range_{b['label']}", color="blue")))
    return msgs


def detect_scenario_type(cfg: dict) -> str:
    if "pipelines" in cfg:  return "inspection"
    if "beacons"   in cfg:  return "gps_denied"
    if "npcs"      in cfg:  return "game"
    return "unknown"


# ---------------------------------------------------------------------------
# Publish
# ---------------------------------------------------------------------------

def publish_visuals(msgs: list, host: str, port: int):
    if not HAS_PYMOOS:
        print("pymoos not installed — printing VIEW_* messages instead:\n")
        for var, val in msgs:
            print(f"  {var} = {val}\n")
        return

    comms = pymoos.comms()
    connected = [False]

    def on_connect():
        connected[0] = True
        return True

    comms.set_on_connect_callback(on_connect)
    comms.run(host, port, "pBriefingVisuals")

    deadline = time.time() + 10
    while not connected[0] and time.time() < deadline:
        time.sleep(0.1)

    if not connected[0]:
        print(f"ERROR: Could not connect to MOOSDB at {host}:{port}")
        return

    t = pymoos.time()
    for var, val in msgs:
        comms.notify(var, val, t)
        time.sleep(0.05)

    time.sleep(0.5)
    comms.close(True)
    print(f"  Posted {len(msgs)} visual messages to shoreside.")


# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Inject static mission visuals into the live pMarineViewer")
    parser.add_argument("--scenario", required=True)
    parser.add_argument("--port", type=int, default=9100,
                        help="Shoreside MOOSDB port (default: 9100)")
    parser.add_argument("--host", default="localhost")
    args = parser.parse_args()

    with open(args.scenario, "rb") as f:
        cfg = tomllib.load(f)

    stype = detect_scenario_type(cfg)
    gen   = {"game":       game_visuals,
             "inspection": inspection_visuals,
             "gps_denied": gps_denied_visuals}.get(stype)

    if gen is None:
        print(f"Unknown scenario type: {stype}")
        sys.exit(1)

    msgs = gen(cfg)
    print(f"Injecting {len(msgs)} visuals for '{stype}' scenario "
          f"at {args.host}:{args.port}…")
    publish_visuals(msgs, args.host, args.port)


if __name__ == "__main__":
    main()
