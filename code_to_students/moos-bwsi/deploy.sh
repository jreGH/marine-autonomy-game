#!/usr/bin/env bash
# deploy.sh — Instructor one-shot mission deployer
#
# Generates mission files from a scenario TOML, copies them to the appropriate
# cloud droplets, and starts the simulation with a single command.
#
# Usage:
#   ./deploy.sh --scenario missions/game/scenarios/scavenger_hunt.toml [--warp 4]
#   ./deploy.sh --scenario missions/inspection/scenarios/pipeline_survey.toml
#   ./deploy.sh --scenario missions/gps_denied/scenarios/beacon_nav.toml --warp 2
#   ./deploy.sh --scenario missions/mcm/scenarios/mcm_example.toml --warp 4
#
# Requirements:
#   - Python 3.11+ (or 3.8+ with tomli) for the gen scripts
#   - ssh key-based access to all droplets (no password prompts)
#   - The scenario TOML must have a [deployment] section with host IPs
#   - docker compose available on each remote droplet
#
# The [deployment] section in your scenario TOML should look like:
#
#   [deployment]
#   shoreside_host = "165.22.100.50"
#
#   [deployment.vehicle_hosts]
#   alpha = "142.93.50.10"
#   bravo = "142.93.50.11"

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ---------------------------------------------------------------------------
# Parse arguments
# ---------------------------------------------------------------------------
SCENARIO=""
WARP=4
OUTDIR="/tmp/bwsi_deploy_$$"
SSH_USER="root"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --scenario) SCENARIO="$2"; shift 2 ;;
        --warp)     WARP="$2";     shift 2 ;;
        --outdir)   OUTDIR="$2";   shift 2 ;;
        --user)     SSH_USER="$2"; shift 2 ;;
        --help|-h)
            sed -n '2,30p' "$0" | grep '^#' | sed 's/^# //'
            exit 0 ;;
        *) echo "Unknown flag: $1"; exit 1 ;;
    esac
done

if [[ -z "$SCENARIO" ]]; then
    echo "ERROR: --scenario is required."
    exit 1
fi

SCENARIO="$(realpath "$SCENARIO")"
echo "=== Generating mission from: $SCENARIO"
echo "=== Output directory:        $OUTDIR"

# ---------------------------------------------------------------------------
# Detect mission type and pick the right generator
# ---------------------------------------------------------------------------
basename_no_ext="$(basename "$SCENARIO" .toml)"

if [[ "$SCENARIO" == */game/* ]]; then
    GEN="$SCRIPT_DIR/missions/game/gen_mission.py"
elif [[ "$SCENARIO" == */inspection/* ]]; then
    GEN="$SCRIPT_DIR/missions/inspection/gen_inspection.py"
elif [[ "$SCENARIO" == */gps_denied/* ]]; then
    GEN="$SCRIPT_DIR/missions/gps_denied/gen_gps_denied.py"
elif [[ "$SCENARIO" == */mcm/* ]]; then
    GEN="$SCRIPT_DIR/missions/mcm/gen_mcm.py"
else
    echo "ERROR: Cannot determine mission type from path: $SCENARIO"
    echo "       Path must contain /game/, /inspection/, /gps_denied/, or /mcm/"
    exit 1
fi

python3 "$GEN" --scenario "$SCENARIO" --outdir "$OUTDIR"

# ---------------------------------------------------------------------------
# Parse deployment section from TOML to get host IPs
# ---------------------------------------------------------------------------
python3 - "$SCENARIO" <<'PYEOF'
import sys, json
try:
    import tomllib
except ImportError:
    import tomli as tomllib  # type: ignore

with open(sys.argv[1], "rb") as f:
    cfg = tomllib.load(f)

deploy = cfg.get("deployment", {})
shore  = deploy.get("shoreside_host", "localhost")
vhosts = deploy.get("vehicle_hosts", {})

if shore == "localhost":
    print("SHORESIDE_HOST=localhost")
    print("IS_LOCAL=true")
else:
    print(f"SHORESIDE_HOST={shore}")
    print("IS_LOCAL=false")
    for team, ip in vhosts.items():
        print(f"VEHICLE_HOST_{team.upper()}={ip}")
PYEOF

# Source the above output to get the variables
eval "$(python3 - "$SCENARIO" <<'PYEOF'
import sys
try:
    import tomllib
except ImportError:
    import tomli as tomllib  # type: ignore

with open(sys.argv[1], "rb") as f:
    cfg = tomllib.load(f)

deploy = cfg.get("deployment", {})
shore  = deploy.get("shoreside_host", "localhost")
vhosts = deploy.get("vehicle_hosts", {})

if shore == "localhost":
    print("SHORESIDE_HOST=localhost")
    print("IS_LOCAL=true")
else:
    print(f"SHORESIDE_HOST={shore}")
    print("IS_LOCAL=false")
    for team, ip in vhosts.items():
        print(f"VEHICLE_HOST_{team.upper()}={ip}")
PYEOF
)"

# ---------------------------------------------------------------------------
# Single-host (local) mode — just run launch_all_local.sh
# ---------------------------------------------------------------------------
if [[ "${IS_LOCAL:-false}" == "true" ]]; then
    echo ""
    echo "=== Local mode: starting all communities on this machine..."
    cd "$OUTDIR"
    exec ./launch_all_local.sh "$WARP"
fi

# ---------------------------------------------------------------------------
# Multi-host mode — distribute files and start containers
# ---------------------------------------------------------------------------
COMPOSE_SHORE="$SCRIPT_DIR/docker/docker-compose.shoreside.yml"
COMPOSE_VEH="$SCRIPT_DIR/docker/docker-compose.vehicle.yml"

echo ""
echo "=== Deploying to Tier 1 ($SHORESIDE_HOST)..."

# Copy shoreside files
SHORE_FILES=(shoreside.moos launch_shoreside.sh)
# Also copy NPC files if any
SHORE_FILES+=( $(ls "$OUTDIR"/*.moos 2>/dev/null | \
    xargs -I{} basename {} .moos | \
    grep -v -f <(python3 - "$SCENARIO" <<'PYEOF'
import sys
try:
    import tomllib
except ImportError:
    import tomli as tomllib
with open(sys.argv[1], "rb") as f:
    cfg = tomllib.load(f)
for t in cfg.get("teams",[]):
    for v in t.get("vehicles",[]):
        print(v["name"])
PYEOF
) | sed 's/$/.moos/' 2>/dev/null || true) )

ssh "${SSH_USER}@${SHORESIDE_HOST}" "mkdir -p /mission /logs"
scp "$COMPOSE_SHORE" "${SSH_USER}@${SHORESIDE_HOST}:/mission/docker-compose.shoreside.yml"
for f in "${SHORE_FILES[@]}"; do
    [[ -f "$OUTDIR/$f" ]] && scp "$OUTDIR/$f" "${SSH_USER}@${SHORESIDE_HOST}:/mission/"
done
# Copy bhv files for NPCs
for f in "$OUTDIR"/*.bhv; do
    scp "$f" "${SSH_USER}@${SHORESIDE_HOST}:/mission/" 2>/dev/null || true
done

echo "=== Starting shoreside..."
ssh "${SSH_USER}@${SHORESIDE_HOST}" \
    "cd /mission && docker compose -f docker-compose.shoreside.yml up -d"

# ---- Vehicle droplets ----
python3 - "$SCENARIO" <<'PYEOF'
import sys
try:
    import tomllib
except ImportError:
    import tomli as tomllib
with open(sys.argv[1], "rb") as f:
    cfg = tomllib.load(f)
deploy = cfg.get("deployment", {})
shore  = deploy.get("shoreside_host", "localhost")
vhosts = deploy.get("vehicle_hosts", {})
teams  = cfg.get("teams", [])
for team in teams:
    tname = team["name"]
    ip    = vhosts.get(tname, shore)
    print(f"{tname} {ip}")
PYEOF | while read tname vip; do
    echo ""
    echo "=== Deploying team $tname to $vip..."
    VFILES=("launch_vehicle_${tname}.sh")
    # Collect .moos and .bhv for this team's vehicles
    python3 - "$SCENARIO" "$tname" <<'PYEOF'
import sys
try:
    import tomllib
except ImportError:
    import tomli as tomllib
with open(sys.argv[1], "rb") as f:
    cfg = tomllib.load(f)
for t in cfg.get("teams", []):
    if t["name"] == sys.argv[2]:
        for v in t.get("vehicles", []):
            print(v["name"])
PYEOF | while read vname; do
        VFILES+=("${vname}.moos" "${vname}.bhv")
    done

    ssh "${SSH_USER}@${vip}" "mkdir -p /mission /logs"
    scp "$COMPOSE_VEH" "${SSH_USER}@${vip}:/mission/docker-compose.vehicle.yml"
    echo "TEAM=${tname}" | ssh "${SSH_USER}@${vip}" "cat > /mission/.env"
    for f in "${VFILES[@]}"; do
        [[ -f "$OUTDIR/$f" ]] && scp "$OUTDIR/$f" "${SSH_USER}@${vip}:/mission/"
    done

    echo "=== Starting vehicle for team $tname on $vip..."
    ssh "${SSH_USER}@${vip}" \
        "cd /mission && TEAM=${tname} docker compose -f docker-compose.vehicle.yml up -d"
done

echo ""
echo "=== Mission running!"
echo "    Dashboard:   http://${SHORESIDE_HOST}:8080"
echo "    MOOS console: ssh ${SSH_USER}@${SHORESIDE_HOST} 'cd /mission && uMAC shoreside.moos'"
echo ""
echo "=== To stop:"
echo "    ssh ${SSH_USER}@${SHORESIDE_HOST} 'cd /mission && docker compose -f docker-compose.shoreside.yml down'"
