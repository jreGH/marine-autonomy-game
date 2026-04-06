#!/usr/bin/env bash
# launch_mcm.sh — convenience wrapper for running a local MCM mission
#
# Usage:
#   ./launch_mcm.sh --scenario scenarios/mcm_example.toml [--warp 4]
#
# This script:
#   1. Generates the mission files from the TOML scenario
#   2. Runs launch_all_local.sh to start all MOOS communities

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCENARIO=""
WARP=1

while [[ $# -gt 0 ]]; do
    case "$1" in
        --scenario|-s) SCENARIO="$2"; shift 2 ;;
        --warp|-w)     WARP="$2";     shift 2 ;;
        --help|-h)
            echo "Usage: $0 --scenario <toml> [--warp <N>]"
            exit 0 ;;
        *) echo "Unknown flag: $1"; exit 1 ;;
    esac
done

if [[ -z "$SCENARIO" ]]; then
    echo "ERROR: --scenario is required."
    echo "Usage: $0 --scenario scenarios/mcm_example.toml [--warp 4]"
    exit 1
fi

# Make the scenario path absolute
SCENARIO="$(realpath "$SCENARIO")"
SCENARIO_BASE="$(basename "$SCENARIO" .toml)"
OUTDIR="$SCRIPT_DIR/run/$SCENARIO_BASE"

echo "=== Generating MCM mission from: $SCENARIO"
python3 "$SCRIPT_DIR/gen_mcm.py" --scenario "$SCENARIO" --outdir "$OUTDIR"

echo ""
echo "=== Starting local mission (warp=$WARP)..."
cd "$OUTDIR"
exec ./launch_all_local.sh "$WARP"
