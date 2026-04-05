#!/usr/bin/env python3
"""
gen_gps_denied.py — BWSI AUVC GPS-denied navigation mission generator
=====================================================================
Usage:
    python gen_gps_denied.py --scenario scenarios/beacon_nav.toml
    python gen_gps_denied.py --scenario scenarios/beacon_nav.toml --outdir /tmp/run
"""

import argparse
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
        print("ERROR: TOML library not found.  Python 3.11+: tomllib is built-in.")
        sys.exit(1)


SHORESIDE_PORT       = 9100
SHORESIDE_SHARE_PORT = 9110
VEHICLE_PORT_START   = 9000
VEHICLE_SHARE_OFFSET = 50


# ---------------------------------------------------------------------------
# Helpers
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


def vertices_to_moos(vertices):
    return ":".join(f"{v[0]},{v[1]}" for v in vertices)


def default_patrol_polygon(start_x, start_y, radius=30):
    r = radius
    return (f"{start_x - r},{start_y + r}:"
            f"{start_x + r},{start_y + r}:"
            f"{start_x + r},{start_y - r}:"
            f"{start_x - r},{start_y - r}")


def beacon_config_blocks(beacons):
    """Build  beacon = x=...,y=...,label=...  lines."""
    return "\n".join(
        f"  beacon = x={b['x']},y={b['y']},label={b['label']}"
        for b in beacons
    )


def beacon_bridge_lines(vehicle_names):
    """Bridge BEACON_RANGE_REPORT_<VNAME> → BEACON_RANGE_REPORT in vehicle community."""
    lines = []
    for vname in vehicle_names:
        vupper = vname.upper()
        lines.append(
            f"  bridge = src=BEACON_RANGE_REPORT_{vupper}, "
            f"alias=BEACON_RANGE_REPORT"
        )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------

def generate(scenario_path, outdir):
    with open(scenario_path, "rb") as f:
        cfg = tomllib.load(f)

    sc         = cfg["scenario"]
    origin     = cfg["origin"]
    arena_v    = cfg["arena"]["vertices"]
    search_v   = cfg["search_box"]["vertices"]
    scoring    = cfg.get("scoring", {})
    acoustic   = cfg.get("acoustic", {})
    dive       = cfg.get("dive", {})
    beacons    = cfg.get("beacons", [])
    teams      = cfg["teams"]

    arena_polygon  = vertices_to_moos(arena_v)
    search_polygon = vertices_to_moos(search_v)
    tiff_file      = sc.get("tiff_file", "MIT_SP.tif")

    all_vehicle_names = [v["name"] for team in teams for v in team["vehicles"]]

    shoreside_tmpl = load_template("shoreside.moos.template")
    vehicle_tmpl   = load_template("vehicle.moos.template")
    vbhv_tmpl      = load_template("vehicle.bhv.template")

    launch_lines = [
        "#!/bin/bash -e",
        "# Auto-generated — do not edit by hand.",
        "",
        "WARP=${1:-1}",
        "cd \"$(dirname \"$0\")\"",
        "",
    ]

    # ---- Shoreside ----
    shoreside_vals = dict(
        SHORESIDE_PORT      = SHORESIDE_PORT,
        SHARE_LISTEN_PORT   = SHORESIDE_SHARE_PORT,
        LAT_ORIGIN          = origin["lat"],
        LON_ORIGIN          = origin["lon"],
        TIFF_FILE           = tiff_file,
        BEACON_BLOCKS       = beacon_config_blocks(beacons),
        PUSH_DIST           = acoustic.get("push_dist",       120.0),
        PULL_DIST           = acoustic.get("pull_dist",       130.0),
        BEACON_FREQ         = acoustic.get("freq",              0.2),
        NOISE_MAGNITUDE     = acoustic.get("noise_magnitude",   2.0),
        BEACON_BRIDGE_LINES = beacon_bridge_lines(all_vehicle_names),
    )
    write_file(os.path.join(outdir, "shoreside.moos"),
               Template(shoreside_tmpl).safe_substitute(shoreside_vals))

    launch_lines += [
        "echo 'Starting shoreside...'",
        f"pAntler shoreside.moos --MOOSTimeWarp=$WARP >& /dev/null &",
        "sleep 1",
        "",
    ]

    # ---- Vehicles ----
    v_port = VEHICLE_PORT_START
    for team in teams:
        for vehicle in team["vehicles"]:
            vname      = vehicle["name"]
            vupper     = vname.upper()
            port       = v_port
            share_port = port + VEHICLE_SHARE_OFFSET

            python_mode = (vehicle.get("student_mode", "cpp").lower() == "python")
            if python_mode:
                pchallenge_run_line  = ""
                pchallenge_cfg_block = ""
            else:
                pchallenge_run_line  = "  Run = pChallenge          @ NewConsole = false\n"
                pchallenge_cfg_block = (
                    "//------------------------------------------\n"
                    "ProcessConfig = pChallenge\n{\n"
                    "  AppTick   = 4\n  CommsTick = 4\n\n"
                    "  min_chase_dist = 5.0\n  max_chase_dist = 50.0\n}"
                )

            v_vals = dict(
                VEHICLE_NAME            = vname,
                VEHICLE_NAME_UPPER      = vupper,
                TEAM_NAME               = team["name"],
                VEHICLE_COLOR           = team["color"],
                SERVER_PORT             = port,
                SHARE_LISTEN_PORT       = share_port,
                SHORESIDE_PORT          = SHORESIDE_PORT,
                LAT_ORIGIN              = origin["lat"],
                LON_ORIGIN              = origin["lon"],
                START_X                 = vehicle["start_x"],
                START_Y                 = vehicle["start_y"],
                START_HEADING           = vehicle.get("start_heading", 180),
                MAX_SPEED               = vehicle.get("max_speed", 3.0),
                ARENA_POLYGON           = arena_polygon,
                PATROL_POLYGON          = search_polygon,   # fallback for moos template
                SEARCH_POLYGON          = search_polygon,
                SEARCH_DEPTH            = dive.get("search_depth",   15.0),
                SURFACE_PERIOD          = dive.get("surface_period",  60.0),
                SURFACE_TIME            = dive.get("surface_time",    20.0),
                PCHALLENGE_RUN_LINE     = pchallenge_run_line,
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
                    f"echo '  NOTE: {vname} in Python mode — "
                    f"run: python student/examples/beacon_nav.py "
                    f"--vehicle {vname} --port {port}'"
                )
            launch_lines.append("")
            v_port += 1

    launch_lines += [
        "echo ''",
        "echo 'All communities started.  Opening mission console...'",
        "uMAC shoreside.moos",
    ]

    write_file(os.path.join(outdir, "launch.sh"),
               "\n".join(launch_lines) + "\n",
               executable=True)

    n_veh = sum(len(t["vehicles"]) for t in teams)
    print(f"\nMission generated in: {outdir}")
    print(f"  Communities: shoreside + {n_veh} vehicle(s)")
    print(f"  Beacons:     {len(beacons)}")
    print(f"\nTo run:")
    print(f"  cd {outdir} && ./launch.sh [time_warp]")


# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="BWSI AUVC GPS-denied navigation mission generator")
    parser.add_argument("--scenario", required=True)
    parser.add_argument("--outdir", default=None)
    args = parser.parse_args()

    if args.outdir is None:
        base = os.path.splitext(os.path.basename(args.scenario))[0]
        args.outdir = os.path.abspath(
            os.path.join(os.path.dirname(args.scenario), "..", "run", base))
    args.outdir = os.path.abspath(args.outdir)

    print(f"Generating GPS-denied mission from: {args.scenario}")
    print(f"Output directory:                   {args.outdir}\n")
    generate(args.scenario, args.outdir)


if __name__ == "__main__":
    main()
