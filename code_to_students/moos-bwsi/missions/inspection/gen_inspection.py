#!/usr/bin/env python3
"""
gen_inspection.py — BWSI AUVC infrastructure inspection mission generator
=========================================================================
Reads a TOML scenario file and produces a runnable MOOS mission directory
configured for the pipeline / cable inspection serious mission.

Usage:
    python gen_inspection.py --scenario scenarios/pipeline_survey.toml
    python gen_inspection.py --scenario scenarios/pipeline_survey.toml --outdir /tmp/run

Outputs (in --outdir, default: run/<scenario_name>/):
    shoreside.moos
    <vehicle>.moos  and  <vehicle>.bhv   for each player vehicle
    launch.sh
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
        print("ERROR: TOML library not found.")
        print("  Python 3.11+: tomllib is in the standard library.")
        print("  Python < 3.11: pip install tomli")
        sys.exit(1)


# ---------------------------------------------------------------------------
# Port allocation (same constants as gen_mission.py for consistency)
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


def default_patrol_polygon(start_x, start_y, radius=30):
    r = radius
    return (f"{start_x - r},{start_y + r}:"
            f"{start_x + r},{start_y + r}:"
            f"{start_x + r},{start_y - r}:"
            f"{start_x - r},{start_y - r}")


def yaml_vertices_to_moos(vertices):
    return ":".join(f"{v[0]},{v[1]}" for v in vertices)


# ---------------------------------------------------------------------------
# Template builders for the inspection-specific config blocks
# ---------------------------------------------------------------------------

def pipeline_config_blocks(pipelines):
    """Build the  pipeline = ...  lines for pInfrastructureSensor config."""
    lines = []
    for pipe in pipelines:
        pts = ":".join(f"{p[0]},{p[1]}" for p in pipe["points"])
        lines.append(
            f"  pipeline = label={pipe['label']},"
            f"depth={pipe['depth']},"
            f"points={pts}"
        )
    return "\n".join(lines)


def anomaly_config_blocks(anomalies):
    """Build the  anomaly = ...  lines for pInfrastructureSensor config."""
    lines = []
    for anom in anomalies:
        lines.append(
            f"  anomaly  = pipeline={anom['pipeline']},"
            f"x={anom['x']},y={anom['y']},"
            f"type={anom['type']}"
        )
    return "\n".join(lines)


def detect_bridge_lines(vehicle_names):
    """
    Build pShare bridge declarations so detection messages reach each vehicle.
    These go inside the uFldShoreBroker ProcessConfig on the shoreside.

    The pattern:
        bridge = src=INFRASTRUCTURE_DETECT_JELLYFISH, alias=INFRASTRUCTURE_DETECT
    means: take INFRASTRUCTURE_DETECT_JELLYFISH from shoreside and publish it
    as INFRASTRUCTURE_DETECT in the jellyfish community.
    """
    lines = []
    for vname in vehicle_names:
        vupper = vname.upper()
        lines.append(
            f"  bridge = src=INFRASTRUCTURE_DETECT_{vupper}, "
            f"alias=INFRASTRUCTURE_DETECT"
        )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main generation logic
# ---------------------------------------------------------------------------

def generate(scenario_path, outdir):
    with open(scenario_path, "rb") as f:
        cfg = tomllib.load(f)

    sc        = cfg["scenario"]
    origin    = cfg["origin"]
    arena_v   = cfg["arena"]["vertices"]
    scoring   = cfg.get("scoring", {})
    sensor    = cfg.get("sensor", {})
    pipelines = cfg.get("pipelines", [])
    anomalies = cfg.get("anomalies", [])
    teams     = cfg["teams"]

    arena_polygon = yaml_vertices_to_moos(arena_v)
    tiff_file     = sc.get("tiff_file", "MIT_SP.tif")

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

    launch_lines = [
        "#!/bin/bash -e",
        "# Auto-generated launch script — do not edit by hand.",
        "",
        "WARP=${1:-1}",
        "cd \"$(dirname \"$0\")\"",
        "",
    ]

    # ---- Shoreside ----
    shoreside_vals = dict(
        SHORESIDE_PORT       = SHORESIDE_PORT,
        SHARE_LISTEN_PORT    = SHORESIDE_SHARE_PORT,
        LAT_ORIGIN           = origin["lat"],
        LON_ORIGIN           = origin["lon"],
        TIFF_FILE            = tiff_file,
        PIPELINE_BLOCKS      = pipeline_config_blocks(pipelines),
        ANOMALY_BLOCKS       = anomaly_config_blocks(anomalies),
        DETECT_RANGE         = sensor.get("detect_range",  30.0),
        DETECT_CONE          = sensor.get("detect_cone",   60.0),
        NOISE_SIGMA          = sensor.get("noise_sigma",    3.0),
        P_FALSE_ALARM        = sensor.get("p_false_alarm", 0.02),
        REVEAL_PIPE          = str(sensor.get("reveal_pipe", False)).lower(),
        DETECT_BRIDGE_LINES  = detect_bridge_lines(all_vehicle_names),
        COVERAGE_SCORE       = scoring.get("coverage_score",   1000),
        COVERAGE_THRESHOLD   = scoring.get("coverage_threshold", 0.8),
        ANOMALY_SCORE        = scoring.get("anomaly_score",     500),
        FALSE_ALARM_PENALTY  = scoring.get("false_alarm_penalty", 100),
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
            vname      = vehicle["name"]
            vupper     = vname.upper()
            port       = v_port
            share_port = port + VEHICLE_SHARE_OFFSET

            patrol = default_patrol_polygon(
                vehicle["start_x"], vehicle["start_y"], radius=30)

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
                MAX_SPEED               = vehicle.get("max_speed", 4.0),
                ARENA_POLYGON           = arena_polygon,
                PATROL_POLYGON          = patrol,
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
                    f"echo '  NOTE: {vname} is in Python mode — "
                    f"run: python student/examples/pipeline_survey.py "
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

    n_vehicles = sum(len(t["vehicles"]) for t in teams)
    print(f"\nMission generated in: {outdir}")
    print(f"  Communities: shoreside + {n_vehicles} vehicle(s)")
    print(f"  Pipelines:   {len(pipelines)}")
    print(f"  Anomalies:   {len(anomalies)}")
    print(f"\nTo run:")
    print(f"  cd {outdir}")
    print(f"  ./launch.sh [time_warp]   # e.g. ./launch.sh 4")


# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="BWSI AUVC infrastructure inspection mission generator")
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
    print(f"Generating inspection mission from: {args.scenario}")
    print(f"Output directory:                   {args.outdir}\n")

    generate(args.scenario, args.outdir)


if __name__ == "__main__":
    main()
