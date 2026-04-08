#!/usr/bin/env python3
"""
gen_mcm.py — BWSI AUVC mine countermeasures mission generator
=============================================================
Reads a TOML scenario file and produces a runnable MOOS mission directory
configured for the MCM serious mission (uFldHazardSensor + uFldHazardMetric).

Usage:
    python gen_mcm.py --scenario scenarios/mcm_example.toml
    python gen_mcm.py --scenario scenarios/mcm_example.toml --outdir /tmp/run

Outputs (in --outdir, default: run/<scenario_name>/):
    shoreside.moos
    <vehicle>.moos  and  <vehicle>.bhv   for each player vehicle
    launch_shoreside.sh
    launch_vehicle_<team>.sh             for each team
    launch_all_local.sh
"""

import argparse
import math
import os
import stat
import sys
from string import Template

try:
    import tomllib
except ImportError:
    try:
        import tomli as tomllib
    except ImportError:
        print("ERROR: TOML library not found.")
        print("  Python 3.11+: tomllib is in the standard library.")
        print("  Python < 3.11: pip install tomli")
        sys.exit(1)


# ---------------------------------------------------------------------------
# Port allocation
# ---------------------------------------------------------------------------
SHORESIDE_PORT       = 9100
SHORESIDE_SHARE_PORT = 9110
VEHICLE_PORT_START   = 9000
VEHICLE_SHARE_OFFSET = 50


# ---------------------------------------------------------------------------
# File helpers
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


def yaml_vertices_to_moos(vertices):
    return ":".join(f"{v[0]},{v[1]}" for v in vertices)


# ---------------------------------------------------------------------------
# MCM-specific template builders
# ---------------------------------------------------------------------------

def hazard_config_blocks(mines):
    """
    Build the  hazard = ...  lines for uFldHazardSensor and uFldHazardMetric.

    Format accepted by both apps:
        hazard = label=m01,x=-80,y=-150,type=hazard
    """
    lines = []
    for mine in mines:
        lines.append(
            f"  hazard = label={mine['label']},"
            f"x={mine['x']},y={mine['y']},"
            f"type={mine['type']}"
        )
    return "\n".join(lines)


def detect_bridge_lines(vehicle_names):
    """
    Build pShare bridge declarations so detection/classification messages
    from uFldHazardSensor reach each vehicle community.

    uFldHazardSensor publishes:
        UHZ_DETECTION_REPORT_JELLYFISH  → bridged to jellyfish as UHZ_DETECTION_REPORT
        UHZ_CLASSIFY_REPORT_JELLYFISH   → bridged to jellyfish as UHZ_CLASSIFY_REPORT
    """
    lines = []
    for vname in vehicle_names:
        vupper = vname.upper()
        lines.append(
            f"  bridge = src=UHZ_DETECTION_REPORT_{vupper}, "
            f"alias=UHZ_DETECTION_REPORT"
        )
        lines.append(
            f"  bridge = src=UHZ_CLASSIFY_REPORT_{vupper},  "
            f"alias=UHZ_CLASSIFY_REPORT"
        )
    return "\n".join(lines)


def lawnmower_points(vertices, lane_width=25.0, x_offset=0.0):
    """
    Generate a systematic lawnmower survey pattern over the bounding box
    of the arena vertices.

    The pattern sweeps from south to north, alternating east and west
    at each lane.  x_offset staggers the starting lane for each vehicle
    so multiple vehicles cover the area without fully overlapping.

    Returns a MOOS-style waypoint string: "x0,y0:x1,y1:..."
    """
    xs = [v[0] for v in vertices]
    ys = [v[1] for v in vertices]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)

    # Shrink slightly inside the arena boundary to avoid OpRegion violations
    margin = lane_width * 0.5
    min_x += margin
    max_x -= margin
    min_y += margin
    max_y -= margin

    pts = []
    y = min_y
    left_to_right = True
    while y <= max_y + lane_width * 0.1:
        if left_to_right:
            pts.append((min_x + x_offset, y))
            pts.append((max_x + x_offset, y))
        else:
            pts.append((max_x + x_offset, y))
            pts.append((min_x + x_offset, y))
        y += lane_width
        left_to_right = not left_to_right

    # Clamp x values inside the arena
    clamped = []
    for x, y in pts:
        x = max(min_x, min(max_x, x))
        clamped.append((x, y))

    return ":".join(f"{x:.1f},{y:.1f}" for x, y in clamped)


# ---------------------------------------------------------------------------
# Main generation logic
# ---------------------------------------------------------------------------

def generate(scenario_path, outdir):
    with open(scenario_path, "rb") as f:
        cfg = tomllib.load(f)

    sc      = cfg["scenario"]
    origin  = cfg["origin"]
    arena_v = cfg["arena"]["vertices"]
    mines   = cfg.get("mines", [])
    sensor  = cfg.get("sensor", {})
    scoring = cfg.get("scoring", {})
    survey  = cfg.get("survey", {})
    teams   = cfg["teams"]

    arena_polygon = yaml_vertices_to_moos(arena_v)
    tiff_file     = sc.get("tiff_file", "MIT_SP.tif")
    lane_width    = survey.get("lane_width",   25.0)
    survey_speed  = survey.get("survey_speed",  2.5)

    # ---- Deployment configuration (optional — defaults to localhost) ----
    deployment     = cfg.get("deployment", {})
    shoreside_host = deployment.get("shoreside_host", "localhost")
    vehicle_hosts  = deployment.get("vehicle_hosts", {})
    headless       = (shoreside_host != "localhost")

    def get_vehicle_host(team_name):
        return vehicle_hosts.get(team_name, shoreside_host)

    viewer_run_line = (
        "  Run = pMarineViewer           @ NewConsole = false\n"
        if not headless else ""
    )
    viewer_config_block = (
        "//------------------------------------------\n"
        "ProcessConfig = pMarineViewer\n"
        "{\n"
        "  AppTick    = 4\n"
        "  CommsTick  = 4\n"
        "\n"
        f"  tiff_file            = {tiff_file}\n"
        "  set_pan_x            = -90\n"
        "  set_pan_y            = 0\n"
        "  zoom                 = 0.5\n"
        "  vehicle_shape_scale  = 1.5\n"
        "  hash_delta           = 500\n"
        "  hash_shade           = 0.22\n"
        "  hash_viewable        = false\n"
        "  trails_point_size    = 1\n"
        "\n"
        "  appcast_height       = 75\n"
        "  appcast_width        = 30\n"
        "  appcast_viewable     = true\n"
        "  appcast_color_scheme = indigo\n"
        "  nodes_font_size      = medium\n"
        "  procs_font_size      = medium\n"
        "  appcast_font_size    = small\n"
        "\n"
        "  scope = NODE_REPORT\n"
        "  scope = UHZ_DETECTION_REPORT\n"
        "  scope = UHZ_CLASSIFY_REPORT\n"
        "  scope = UHZ_HAZARD_REPORT\n"
        "\n"
        "  button_one = DEPLOY  # DEPLOY_ALL=true\n"
        "  button_two = HALT    # DEPLOY_ALL=false\n"
        "}\n"
        if not headless else ""
    )

    # Collect all vehicle names for bridge generation
    all_vehicle_names = [
        v["name"]
        for team in teams
        for v in team["vehicles"]
    ]

    # ---- Load templates ----
    shoreside_tmpl = load_template("shoreside.moos.template")
    vehicle_tmpl   = load_template("vehicle.moos.template")
    vbhv_tmpl      = load_template("vehicle.bhv.template")

    shore_lines = [
        "#!/bin/bash -e",
        "# Shoreside launcher — run on the simulation server.",
        "# Auto-generated by gen_mcm.py — do not edit by hand.",
        "",
        "WARP=${1:-1}",
        "cd \"$(dirname \"$0\")\"",
        "",
    ]
    vehicle_lines_by_team = {}
    launch_lines = [
        "#!/bin/bash -e",
        "# Combined launcher (single-host / local mode).",
        "# Auto-generated by gen_mcm.py — do not edit by hand.",
        "",
        "WARP=${1:-1}",
        "cd \"$(dirname \"$0\")\"",
        "",
    ]

    # ---- Shoreside ----
    shoreside_vals = dict(
        SHORESIDE_HOST        = shoreside_host,
        SHORESIDE_PORT        = SHORESIDE_PORT,
        SHARE_LISTEN_PORT     = SHORESIDE_SHARE_PORT,
        LAT_ORIGIN            = origin["lat"],
        LON_ORIGIN            = origin["lon"],
        TIFF_FILE             = tiff_file,
        HAZARD_BLOCKS         = hazard_config_blocks(mines),
        SENSOR_PD             = sensor.get("sensor_pd",     0.85),
        SENSOR_PFA            = sensor.get("sensor_pfa",    0.04),
        SENSOR_WIDTH          = sensor.get("sensor_width",  25.0),
        SENSOR_EXP            = sensor.get("sensor_exp",     6.0),
        CLASSIFY_PD           = sensor.get("classify_pd",   0.75),
        CLASSIFY_TIME         = sensor.get("classify_time", 10.0),
        PENALTY_MISSED        = scoring.get("penalty_missed_hazard",   150),
        PENALTY_FALSE_ALARM   = scoring.get("penalty_false_alarm",      75),
        MAX_TIME              = scoring.get("max_time",                900),
        PENALTY_MAX_TIME_OVER = scoring.get("penalty_max_time_over",   200),
        PENALTY_MAX_TIME_RATE = scoring.get("penalty_max_time_rate",  0.45),
        DETECT_BRIDGE_LINES   = detect_bridge_lines(all_vehicle_names),
        VIEWER_RUN_LINE       = viewer_run_line,
        VIEWER_CONFIG_BLOCK   = viewer_config_block,
    )
    write_file(os.path.join(outdir, "shoreside.moos"),
               Template(shoreside_tmpl).safe_substitute(shoreside_vals))

    shore_lines.append("echo 'Starting shoreside...'")
    shore_lines.append(f"pAntler shoreside.moos --MOOSTimeWarp=$WARP >& /dev/null &")
    shore_lines.append("sleep 1")
    shore_lines.append("")
    launch_lines.append("echo 'Starting shoreside...'")
    launch_lines.append(f"pAntler shoreside.moos --MOOSTimeWarp=$WARP >& /dev/null &")
    launch_lines.append("sleep 1")
    launch_lines.append("")

    # ---- Player vehicles ----
    # Stagger lawnmower start lanes so multiple vehicles don't fully overlap.
    v_port = VEHICLE_PORT_START
    vehicle_index = 0
    for team in teams:
        tname  = team["name"]
        v_host = get_vehicle_host(tname)
        team_lines = vehicle_lines_by_team.setdefault(tname, [
            "#!/bin/bash -e",
            f"# Vehicle launcher for team {tname}.",
            "# Auto-generated by gen_mcm.py — do not edit by hand.",
            "",
            "WARP=${1:-1}",
            "cd \"$(dirname \"$0\")\"",
            "",
        ])

        for vehicle in team["vehicles"]:
            vname      = vehicle["name"]
            vupper     = vname.upper()
            port       = v_port
            share_port = port + VEHICLE_SHARE_OFFSET
            max_speed  = vehicle.get("max_speed", 4.0)

            # Stagger lawnmower lanes: vehicle_index * half a lane_width
            x_offset = vehicle_index * (lane_width * 0.5)
            survey_pts = lawnmower_points(arena_v, lane_width=lane_width,
                                          x_offset=x_offset)

            v_vals = dict(
                VEHICLE_NAME       = vname,
                VEHICLE_NAME_UPPER = vupper,
                TEAM_NAME          = tname,
                VEHICLE_COLOR      = team["color"],
                VEHICLE_HOST       = v_host,
                SHORESIDE_HOST     = shoreside_host,
                SERVER_PORT        = port,
                SHARE_LISTEN_PORT    = share_port,
                SHORESIDE_PORT       = SHORESIDE_PORT,
                SHORESIDE_SHARE_PORT = SHORESIDE_SHARE_PORT,
                LAT_ORIGIN           = origin["lat"],
                LON_ORIGIN         = origin["lon"],
                START_X            = vehicle["start_x"],
                START_Y            = vehicle["start_y"],
                START_HEADING      = vehicle.get("start_heading", 180),
                MAX_SPEED          = max_speed,
                ARENA_POLYGON      = arena_polygon,
                SURVEY_POINTS      = survey_pts,
                SURVEY_SPEED       = survey_speed,
            )
            write_file(os.path.join(outdir, f"{vname}.moos"),
                       Template(vehicle_tmpl).safe_substitute(v_vals))
            write_file(os.path.join(outdir, f"{vname}.bhv"),
                       Template(vbhv_tmpl).safe_substitute(v_vals))

            team_lines.append(f"echo 'Starting vehicle: {vname} (team {tname})'")
            team_lines.append(f"pAntler {vname}.moos --MOOSTimeWarp=$WARP >& /dev/null &")
            team_lines.append("sleep 0.5")

            python_mode = (vehicle.get("student_mode", "cpp").lower() == "python")
            if python_mode:
                note = (
                    f"echo '  NOTE: {vname} is in Python mode — "
                    f"run: python student/examples/mcm_survey.py "
                    f"--vehicle {vname} --host {v_host} --port {port}'"
                )
                team_lines.append(note)

            launch_lines.append(f"echo 'Starting vehicle: {vname} (team {tname})'")
            launch_lines.append(f"pAntler {vname}.moos --MOOSTimeWarp=$WARP >& /dev/null &")
            launch_lines.append("sleep 0.5")
            if python_mode:
                launch_lines.append(note)
            launch_lines.append("")

            v_port += 1
            vehicle_index += 1

    shore_lines += [
        "echo ''",
        "echo 'Shoreside started.  Opening mission console...'",
        "uMAC shoreside.moos",
    ]
    write_file(os.path.join(outdir, "launch_shoreside.sh"),
               "\n".join(shore_lines) + "\n",
               executable=True)

    for tname, lines in vehicle_lines_by_team.items():
        lines += ["echo ''", f"echo 'Vehicle(s) for team {tname} started.'"]
        write_file(os.path.join(outdir, f"launch_vehicle_{tname}.sh"),
                   "\n".join(lines) + "\n",
                   executable=True)

    launch_lines += [
        "echo ''",
        "echo 'All communities started.  Opening mission console...'",
        "uMAC shoreside.moos",
    ]
    write_file(os.path.join(outdir, "launch_all_local.sh"),
               "\n".join(launch_lines) + "\n",
               executable=True)

    n_vehicles = sum(len(t["vehicles"]) for t in teams)
    n_hazards  = sum(1 for m in mines if m["type"] == "hazard")
    n_benign   = sum(1 for m in mines if m["type"] == "benign")
    print(f"\nMission generated in: {outdir}")
    print(f"  Communities: shoreside + {n_vehicles} vehicle(s)")
    print(f"  Mines: {n_hazards} hazard, {n_benign} benign  ({len(mines)} total)")
    if headless:
        print(f"  Deployment:  shoreside={shoreside_host}")
        print(f"\nTo run (multi-host):")
        print(f"  On simulation server: ./launch_shoreside.sh [warp]")
        for tname in vehicle_lines_by_team:
            print(f"  On {get_vehicle_host(tname)} (team {tname}): "
                  f"./launch_vehicle_{tname}.sh [warp]")
    else:
        print(f"\nTo run (single-host / local):")
        print(f"  cd {outdir}")
        print(f"  ./launch_all_local.sh [time_warp]   # e.g. ./launch_all_local.sh 4")


# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="BWSI AUVC MCM mission generator")
    parser.add_argument("--scenario", required=True,
                        help="Path to scenario TOML file")
    parser.add_argument("--outdir", default=None,
                        help="Output directory (default: run/<scenario_name>/)")
    args = parser.parse_args()

    if args.outdir is None:
        scenario_dir  = os.path.dirname(os.path.abspath(args.scenario))
        scenario_base = os.path.splitext(os.path.basename(args.scenario))[0]
        args.outdir   = os.path.join(scenario_dir, "..", "run", scenario_base)

    args.outdir = os.path.abspath(args.outdir)
    print(f"Generating MCM mission from: {args.scenario}")
    print(f"Output directory:            {args.outdir}\n")

    generate(args.scenario, args.outdir)


if __name__ == "__main__":
    main()
