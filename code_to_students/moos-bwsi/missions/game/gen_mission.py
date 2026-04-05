#!/usr/bin/env python3
"""
gen_mission.py — BWSI AUVC mission generator
Reads a YAML scenario file and produces a runnable MOOS mission directory.

Usage:
    python gen_mission.py --scenario scenarios/scavenger_hunt.toml
    python gen_mission.py --scenario scenarios/scavenger_hunt.toml --outdir /tmp/my_run

Outputs (in --outdir, default: run/):
    shoreside.moos
    <vehicle>.moos  and  <vehicle>.bhv   for each player vehicle
    <npc>.moos      and  <npc>.bhv       for each NPC
    launch.sh                             master launch script
"""

import argparse
import os
import stat
import sys
from string import Template

try:
    import tomllib                  # Python 3.11+ stdlib
except ImportError:
    try:
        import tomli as tomllib     # pip install tomli  (Python < 3.11)
    except ImportError:
        print("ERROR: TOML library not found.")
        print("  Python 3.11+: tomllib is included in the standard library.")
        print("  Python < 3.11: pip install tomli")
        sys.exit(1)


# ---------------------------------------------------------------------------
# Port allocation
# ---------------------------------------------------------------------------
SHORESIDE_PORT       = 9100
SHORESIDE_SHARE_PORT = 9110  # pShare listen port for shoreside
VEHICLE_PORT_START   = 9000  # vehicles: 9000, 9001, …
VEHICLE_SHARE_OFFSET = 50    # vehicle pShare listen = vehicle_port + 50
NPC_PORT_START       = 9200  # NPCs: 9200, 9201, …
NPC_SHARE_OFFSET     = 50


# ---------------------------------------------------------------------------
# NPC type metadata
# ---------------------------------------------------------------------------
NPC_COLORS = {
    "shark":    "red",
    "fish":     "cyan",
    "whale":    "white",
    "treasure": "gold",
}

NPC_APPS = {
    "shark":    "pChallenge_shark",
    "fish":     "pChallenge_fish",
    "whale":    "pChallenge_whale",
    "treasure": "pChallenge_treasure",
}

# Config block written into the ProcessConfig of each NPC app
def npc_app_config(npc):
    t = npc["type"]
    lines = [f"name = {npc['name']}"]
    if t in ("shark", "fish", "whale", "treasure"):
        lines.append(f"min_chase_dist = {npc.get('min_chase_dist', 5.0)}")
    if t in ("shark", "fish", "whale"):
        lines.append(f"max_chase_dist = {npc.get('max_chase_dist', 40.0)}")
    if t == "shark":
        lines.append(f"chase_timeout    = {npc.get('chase_timeout', 30.0)}")
        lines.append(f"recovery_timeout = {npc.get('recovery_timeout', 120.0)}")
    if t == "whale":
        lines.append(f"surface_depth_threshold = {npc.get('surface_depth_threshold', 5.0)}")
    if t == "treasure":
        lines.append(f"boundary_radius = {npc.get('boundary_radius', 1500.0)}")
    return "\n  ".join(lines)


# Behavior blocks for each NPC type, inserted into npc.bhv.template
def npc_behavior_block(npc, arena_polygon):
    t = npc["type"]
    patrol = npc.get("patrol_polygon", arena_polygon)
    speed  = npc.get("patrol_speed", 1.5)
    color  = NPC_COLORS.get(t, "white")

    if t == "shark":
        return f"""\
// ----- Shark behaviors -----
initialize CHASE  = false

Set MODE = Chasing {{
  MODE  = Active
  CHASE = true
}} Patrolling

Behavior = BHV_CutRange
{{
  name      = shark_chase
  pwt       = 200
  condition = MODE == Chasing
  updates   = CHASE_UPDATES

  contact        = nobody
  pwt_outer_dist = 80
  pwt_inner_dist = 5
  giveup_dist    = 80

  visual_hints = edge_color={color}, edge_size=1
}}

Behavior = BHV_Loiter
{{
  name      = shark_patrol
  pwt       = 100
  condition = MODE == Patrolling

  polygon        = {patrol}
  clockwise      = true
  speed          = {speed}
  radius         = 15
  nm_radius      = 20
  center_activate = true

  visual_hints = edge_color={color}, edge_size=1
}}"""

    elif t in ("fish", "whale"):
        avoid_var = "AVOID_UPDATES"
        return f"""\
// ----- {t.capitalize()} behaviors -----
initialize ESCAPE = false

Set MODE = Fleeing {{
  MODE   = Active
  ESCAPE = true
}} Patrolling

Behavior = BHV_AvoidCollision
{{
  name      = escape
  pwt       = 200
  condition = MODE == Fleeing
  updates   = {avoid_var}

  contact_type_required = any
  pwt_inner_dist        = 5
  pwt_outer_dist        = 40
  completed_dist        = 60
  min_util_cpa_dist     = 5
  max_util_cpa_dist     = 30
  turn_towards_contact  = false
}}

Behavior = BHV_Loiter
{{
  name      = patrol
  pwt       = 100
  condition = MODE == Patrolling

  polygon        = {patrol}
  clockwise      = true
  speed          = {speed}
  radius         = 12
  nm_radius      = 18
  center_activate = true

  visual_hints = edge_color={color}, edge_size=1
}}"""

    elif t == "treasure":
        return f"""\
// ----- Treasure behaviors -----
initialize WAIT   = true
initialize FOLLOW = false

Set MODE = Following {{
  MODE   = Active
  FOLLOW = true
}} Waiting

Behavior = BHV_Trail
{{
  name      = follow_carrier
  pwt       = 200
  condition = MODE == Following
  updates   = FOLLOW_UPDATES

  contact       = nobody
  trail_range   = 2.0
  trail_angle   = 0.0
  pwt_outer_dist = 20

  visual_hints = edge_color={color}, edge_size=1
}}

Behavior = BHV_StationKeep
{{
  name      = wait_here
  pwt       = 100
  condition = MODE == Waiting

  center_activate    = true
  inner_radius       = 2
  outer_radius       = 10
  outer_speed        = 1.0
  transit_speed      = 1.5

  visual_hints = edge_color={color}, edge_size=1
}}"""

    return "// (no behavior block for this NPC type)"


# ---------------------------------------------------------------------------
# Polygon formatting helpers
# ---------------------------------------------------------------------------
def yaml_vertices_to_moos(vertices):
    """Convert [[x,y], ...] list to MOOS polygon string 'x,y:x,y:...'"""
    return ":".join(f"{v[0]},{v[1]}" for v in vertices)


def default_patrol_polygon(start_x, start_y, radius=60):
    """Fallback patrol square centred on start position."""
    r = radius
    return (f"{start_x - r},{start_y + r}:"
            f"{start_x + r},{start_y + r}:"
            f"{start_x + r},{start_y - r}:"
            f"{start_x - r},{start_y - r}")


# ---------------------------------------------------------------------------
# File loading helpers
# ---------------------------------------------------------------------------
def load_template(name):
    here = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(here, "templates", name)
    with open(path) as f:
        return f.read()


def write_file(path, content, executable=False):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(content)
    if executable:
        st = os.stat(path)
        os.chmod(path, st.st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
    print(f"  wrote {path}")


# ---------------------------------------------------------------------------
# Main generation logic
# ---------------------------------------------------------------------------
def generate(scenario_path, outdir):
    with open(scenario_path, "rb") as f:
        cfg = tomllib.load(f)

    sc      = cfg["scenario"]
    origin  = cfg["origin"]
    arena_v = cfg["arena"]["vertices"]
    game    = cfg["game"]
    teams   = cfg["teams"]
    npcs    = cfg.get("npcs", [])

    arena_polygon = yaml_vertices_to_moos(arena_v)
    tiff_file     = sc.get("tiff_file", "MIT_SP.tif")

    vehicle_tmpl   = load_template("vehicle.moos.template")
    vbhv_tmpl      = load_template("vehicle.bhv.template")
    npc_tmpl       = load_template("npc.moos.template")
    nbhv_tmpl      = load_template("npc.bhv.template")
    shoreside_tmpl = load_template("shoreside.moos.template")

    launch_lines = ["#!/bin/bash -e",
                    "# Auto-generated launch script — do not edit by hand.",
                    "",
                    "WARP=${1:-1}",
                    "cd \"$(dirname \"$0\")\"",
                    ""]

    # ---- Shoreside ----
    shoreside_vals = dict(
        SHORESIDE_PORT     = SHORESIDE_PORT,
        SHARE_LISTEN_PORT  = SHORESIDE_SHARE_PORT,
        LAT_ORIGIN         = origin["lat"],
        LON_ORIGIN         = origin["lon"],
        TIFF_FILE          = tiff_file,
        GAME_LENGTH_MIN    = game["length_min"],
        WHALE_SCORE        = game["whale_score"],
        FISH_SCORE         = game["fish_score"],
        PICKUP_SCORE       = game["pickup_score"],
        COLLECT_SCORE      = game["collect_score"],
        BITE_TIMEOUT       = game["bite_timeout"],
    )
    write_file(os.path.join(outdir, "shoreside.moos"),
               Template(shoreside_tmpl).safe_substitute(shoreside_vals))

    launch_lines.append("echo 'Starting shoreside...'")
    launch_lines.append(f"pAntler shoreside.moos --MOOSTimeWarp=$WARP >& /dev/null &")
    launch_lines.append("sleep 1")
    launch_lines.append("")

    # ---- Player vehicles ----
    v_port = VEHICLE_PORT_START
    for team in teams:
        for vehicle in team["vehicles"]:
            vname  = vehicle["name"]
            vupper = vname.upper()
            port   = v_port
            share_port = port + VEHICLE_SHARE_OFFSET

            # Default patrol polygon: small square around start
            patrol = default_patrol_polygon(
                vehicle["start_x"], vehicle["start_y"], radius=30)

            # student_mode = "python" omits pChallenge so students drive via
            # VehicleAPI.py instead of the C++ app.
            python_mode = (vehicle.get("student_mode", "cpp").lower() == "python")
            if python_mode:
                pchallenge_run_line  = ""
                pchallenge_cfg_block = ""
            else:
                pchallenge_run_line  = "  Run = pChallenge          @ NewConsole = false\n"
                pchallenge_cfg_block = (
                    "//------------------------------------------\n"
                    "ProcessConfig = pChallenge\n"
                    "{\n"
                    "  AppTick   = 4\n"
                    "  CommsTick = 4\n\n"
                    "  min_chase_dist = 5.0\n"
                    "  max_chase_dist = 50.0\n"
                    "}"
                )

            v_vals = dict(
                VEHICLE_NAME           = vname,
                VEHICLE_NAME_UPPER     = vupper,
                TEAM_NAME              = team["name"],
                VEHICLE_COLOR          = team["color"],
                SERVER_PORT            = port,
                SHARE_LISTEN_PORT      = share_port,
                SHORESIDE_PORT         = SHORESIDE_PORT,
                LAT_ORIGIN             = origin["lat"],
                LON_ORIGIN             = origin["lon"],
                START_X                = vehicle["start_x"],
                START_Y                = vehicle["start_y"],
                START_HEADING          = vehicle.get("start_heading", 180),
                MAX_SPEED              = vehicle.get("max_speed", 4.0),
                ARENA_POLYGON          = arena_polygon,
                PATROL_POLYGON         = patrol,
                PCHALLENGE_RUN_LINE    = pchallenge_run_line,
                PCHALLENGE_CONFIG_BLOCK = pchallenge_cfg_block,
            )
            write_file(os.path.join(outdir, f"{vname}.moos"),
                       Template(vehicle_tmpl).safe_substitute(v_vals))
            write_file(os.path.join(outdir, f"{vname}.bhv"),
                       Template(vbhv_tmpl).safe_substitute(v_vals))

            tname = team["name"]
            launch_lines.append(f"echo 'Starting vehicle: {vname} (team {tname})'")
            launch_lines.append(f"pAntler {vname}.moos --MOOSTimeWarp=$WARP >& /dev/null &")
            launch_lines.append("sleep 0.5")
            if python_mode:
                launch_lines.append(
                    f"echo '  NOTE: {vname} is in Python mode — "
                    f"run: python student/examples/chase_nearest.py "
                    f"--vehicle {vname} --port {port}'"
                )

            v_port += 1

    launch_lines.append("")

    # ---- NPCs ----
    npc_port = NPC_PORT_START
    for npc in npcs:
        nname  = npc["name"]
        ntype  = npc["type"]
        napp   = NPC_APPS[ntype]
        ncolor = NPC_COLORS.get(ntype, "white")
        port   = npc_port
        share_port = port + NPC_SHARE_OFFSET

        patrol = npc.get("patrol_polygon",
                         default_patrol_polygon(npc["start_x"], npc["start_y"]))

        n_vals = dict(
            NPC_NAME          = nname,
            NPC_TYPE          = ntype,
            NPC_APP           = napp,
            NPC_APP_TITLE     = ntype.capitalize(),
            NPC_COLOR         = ncolor,
            SERVER_PORT       = port,
            SHARE_LISTEN_PORT = share_port,
            SHORESIDE_PORT    = SHORESIDE_PORT,
            LAT_ORIGIN        = origin["lat"],
            LON_ORIGIN        = origin["lon"],
            START_X           = npc["start_x"],
            START_Y           = npc["start_y"],
            START_HEADING     = npc.get("start_heading", 0),
            ARENA_POLYGON     = arena_polygon,
            NPC_APP_CONFIG    = npc_app_config(npc),
        )
        write_file(os.path.join(outdir, f"{nname}.moos"),
                   Template(npc_tmpl).safe_substitute(n_vals))

        nbhv_vals = dict(
            NPC_NAME          = nname,
            NPC_TYPE          = ntype,
            ARENA_POLYGON     = arena_polygon,
            NPC_BEHAVIOR_BLOCK = npc_behavior_block(npc, patrol),
        )
        write_file(os.path.join(outdir, f"{nname}.bhv"),
                   Template(nbhv_tmpl).safe_substitute(nbhv_vals))

        launch_lines.append(f"echo 'Starting NPC: {nname} ({ntype})'")
        launch_lines.append(f"pAntler {nname}.moos --MOOSTimeWarp=$WARP >& /dev/null &")
        launch_lines.append("sleep 0.5")
        npc_port += 1

    launch_lines += [
        "",
        "echo ''",
        "echo 'All communities started.  Opening mission console...'",
        "uMAC shoreside.moos",
    ]

    write_file(os.path.join(outdir, "launch.sh"),
               "\n".join(launch_lines) + "\n",
               executable=True)

    print(f"\nMission generated in: {outdir}")
    print(f"  Communities: shoreside + "
          f"{sum(len(t['vehicles']) for t in teams)} vehicle(s) + "
          f"{len(npcs)} NPC(s)")
    print(f"\nTo run:")
    print(f"  cd {outdir}")
    print(f"  ./launch.sh [time_warp]   # e.g. ./launch.sh 4")


# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="BWSI AUVC mission generator")
    parser.add_argument("--scenario", required=True,
                        help="Path to scenario YAML file")
    parser.add_argument("--outdir", default=None,
                        help="Output directory (default: run/ next to scenario file)")
    args = parser.parse_args()

    if args.outdir is None:
        scenario_dir  = os.path.dirname(os.path.abspath(args.scenario))
        scenario_base = os.path.splitext(os.path.basename(args.scenario))[0]
        args.outdir   = os.path.join(scenario_dir, "..", "run", scenario_base)

    args.outdir = os.path.abspath(args.outdir)
    print(f"Generating mission from: {args.scenario}")
    print(f"Output directory:        {args.outdir}\n")

    generate(args.scenario, args.outdir)


if __name__ == "__main__":
    main()
