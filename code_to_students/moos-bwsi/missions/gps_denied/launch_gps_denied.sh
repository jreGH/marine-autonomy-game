#!/bin/bash -e
# launch_gps_denied.sh — BWSI AUVC GPS-denied navigation launcher
SCENARIO="beacon_nav"
WARP=1
CLEAN="no"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

SHORT=s:,w:,c,h
LONG=scenario:,warp:,clean,help
OPTS=$(getopt --options $SHORT --longoptions $LONG -- "$@")
[ $? != 0 ] && { echo "Terminating..." >&2; exit 1; }
eval set -- "$OPTS"

while true; do
  case "$1" in
    -s|--scenario) SCENARIO=$2; shift 2 ;;
    -w|--warp)     WARP=$2;     shift 2 ;;
    -c|--clean)    CLEAN="yes"; shift   ;;
    -h|--help)
      echo "Usage: ./launch_gps_denied.sh [--scenario NAME] [--warp N] [--clean]"
      echo "Available scenarios:"; ls "${SCRIPT_DIR}/scenarios/" | sed 's/\.toml//'|sed 's/^/  /'
      exit 0 ;;
    --) shift; break ;;
    *) echo "Unexpected option: $1"; break ;;
  esac
done

SCENARIO_FILE="${SCRIPT_DIR}/scenarios/${SCENARIO}.toml"
RUN_DIR="${SCRIPT_DIR}/run/${SCENARIO}"

[ ! -f "$SCENARIO_FILE" ] && {
  echo "ERROR: Scenario not found: $SCENARIO_FILE"; exit 1; }
[ "$CLEAN" = "yes" ] && [ -d "$RUN_DIR" ] && rm -rf "$RUN_DIR"

echo "Generating mission: $SCENARIO"
python3 "${SCRIPT_DIR}/gen_gps_denied.py" --scenario "$SCENARIO_FILE" --outdir "$RUN_DIR"

echo ""
echo "Generating mission briefing..."
python3 "${SCRIPT_DIR}/../../briefing/gen_briefing.py" \
  --scenario "$SCENARIO_FILE" \
  --output   "${RUN_DIR}/briefing.png" \
  --no-show  2>/dev/null \
  || echo "  (briefing graphic skipped — pip install matplotlib to enable)"

echo ""
echo "Launching with TIME_WARP=$WARP  |  Run dir: $RUN_DIR"
echo ""
cd "$RUN_DIR"
exec ./launch.sh "$WARP"
