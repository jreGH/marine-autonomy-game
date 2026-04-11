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
        "  scope = VIEW_POLYGON\n"
        "  scope = VIEW_SEGLIST\n"
        "  scope = VIEW_POINT\n"
        "  scope = INFRASTRUCTURE_DETECT_JELLYFISH\n"
        "  scope = INFRASTRUCTURE_DETECT_SQUID\n"
        "\n"
        "  button_one = DEPLOY  # DEPLOY_ALL=true\n"
        "  button_two = HALT    # DEPLOY_ALL=false\n"
        "}\n"
        if not headless else ""
    )

    # ---- Load templates ----
    shoreside_tmpl = load_template("shoreside.moos.template")
    vehicle_tmpl   = load_template("vehicle.moos.template")
    vbhv_tmpl      = load_template("vehicle.bhv.template")

    shore_lines = [
        "#!/bin/bash -e",
        "# Shoreside launcher — run on the simulation server.",
        "# Auto-generated by gen_inspection.py — do not edit by hand.",
        "",
        "WARP=${1:-1}",
        "cd \"$(dirname \"$0\")\"",
        "",
    ]
    vehicle_lines_by_team = {}
    launch_lines = [
        "#!/bin/bash -e",
        "# Combined launcher (single-host / local mode).",
        "# Auto-generated by gen_inspection.py — do not edit by hand.",
        "",
        "WARP=${1:-1}",
        "cd \"$(dirname \"$0\")\"",
        "",
    ]

    # ---- Pre-calculate vehicle pShare routes for static DEPLOY routing ----
    # Shore's pShare needs a static output line for each vehicle so that
    # DEPLOY_ALL posted on shore reaches every vehicle as DEPLOY without
    # relying on the dynamic uFldNodeBroker/uFldShoreBroker bridge setup.
    _tmp_port = VEHICLE_PORT_START
    _deploy_outputs = []
    for _team in teams:
        _v_host = get_vehicle_host(_team["name"])
        for _v in _team["vehicles"]:
            _sp = _tmp_port + VEHICLE_SHARE_OFFSET
            _deploy_outputs.append(
                f"  output = src=DEPLOY_ALL, route={_v_host}:{_sp}, alias=DEPLOY")
            _tmp_port += 1
    vehicle_share_outputs = "\n".join(_deploy_outputs)

    # ---- Shoreside ----
    pipeline_blocks = pipeline_config_blocks(pipelines)
    anomaly_blocks  = anomaly_config_blocks(anomalies)

    shoreside_vals = dict(
        SHORESIDE_HOST       = shoreside_host,
        SHORESIDE_PORT       = SHORESIDE_PORT,
        SHARE_LISTEN_PORT    = SHORESIDE_SHARE_PORT,
        LAT_ORIGIN           = origin["lat"],
        LON_ORIGIN           = origin["lon"],
        TIFF_FILE            = tiff_file,
        PIPELINE_BLOCKS      = pipeline_blocks,
        ANOMALY_BLOCKS       = anomaly_blocks,
        DETECT_RANGE         = sensor.get("detect_range", 30.0),
        COVERAGE_SCORE       = scoring.get("coverage_score",   1000),
        COVERAGE_THRESHOLD   = scoring.get("coverage_threshold", 0.8),
        ANOMALY_SCORE        = scoring.get("anomaly_score",     500),
        FALSE_ALARM_PENALTY  = scoring.get("false_alarm_penalty", 100),
        VIEWER_RUN_LINE      = viewer_run_line,
        VIEWER_CONFIG_BLOCK  = viewer_config_block,
        VEHICLE_SHARE_OUTPUTS = vehicle_share_outputs,
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
    v_port = VEHICLE_PORT_START
    for team in teams:
        tname  = team["name"]
        v_host = get_vehicle_host(tname)
        team_lines = vehicle_lines_by_team.setdefault(tname, [
            "#!/bin/bash -e",
            f"# Vehicle launcher for team {tname}.",
            "# Auto-generated by gen_inspection.py — do not edit by hand.",
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
                TEAM_NAME               = tname,
                VEHICLE_COLOR           = team["color"],
                VEHICLE_HOST            = v_host,
                SHORESIDE_HOST          = shoreside_host,
                SERVER_PORT             = port,
                SHARE_LISTEN_PORT       = share_port,
                SHORESIDE_PORT          = SHORESIDE_PORT,
                SHORESIDE_SHARE_PORT    = SHORESIDE_SHARE_PORT,
                LAT_ORIGIN              = origin["lat"],
                LON_ORIGIN              = origin["lon"],
                START_X                 = vehicle["start_x"],
                START_Y                 = vehicle["start_y"],
                START_HEADING           = vehicle.get("start_heading", 180),
                MAX_SPEED               = vehicle.get("max_speed", 4.0),
                ARENA_POLYGON           = arena_polygon,
                PATROL_POLYGON          = patrol,
                PIPELINE_BLOCKS         = pipeline_blocks,
                ANOMALY_BLOCKS          = anomaly_blocks,
                DETECT_RANGE            = sensor.get("detect_range",  30.0),
                DETECT_CONE             = sensor.get("detect_cone",   60.0),
                NOISE_SIGMA             = sensor.get("noise_sigma",    3.0),
                P_FALSE_ALARM           = sensor.get("p_false_alarm", 0.02),
                REVEAL_PIPE             = str(sensor.get("reveal_pipe", False)).lower(),
                PCHALLENGE_RUN_LINE     = pchallenge_run_line,
                PCHALLENGE_CONFIG_BLOCK = pchallenge_cfg_block,
            )
            write_file(os.path.join(outdir, f"{vname}.moos"),
                       Template(vehicle_tmpl).safe_substitute(v_vals))
            write_file(os.path.join(outdir, f"{vname}.bhv"),
                       Template(vbhv_tmpl).safe_substitute(v_vals))

            team_lines.append(f"echo 'Starting vehicle: {vname} (team {tname})'")
            team_lines.append(f"pAntler {vname}.moos --MOOSTimeWarp=$WARP >& /dev/null &")
            team_lines.append("sleep 0.5")
            launch_lines.append(f"echo 'Starting vehicle: {vname} (team {tname})'")
            launch_lines.append(f"pAntler {vname}.moos --MOOSTimeWarp=$WARP >& /dev/null &")
            launch_lines.append("sleep 0.5")
            if python_mode:
                note = (
                    f"echo '  NOTE: {vname} is in Python mode — "
                    f"run: python student/examples/pipeline_survey.py "
                    f"--vehicle {vname} --host {v_host} --port {port}'"
                )
                team_lines.append(note)
                launch_lines.append(note)
            launch_lines.append("")
            v_port += 1

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
    print(f"\nMission generated in: {outdir}")
    print(f"  Communities: shoreside + {n_vehicles} vehicle(s)")
    print(f"  Pipelines:   {len(pipelines)}")
    print(f"  Anomalies:   {len(anomalies)}")
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
