#!/bin/bash -e
# launch_inspection.sh — BWSI AUVC infrastructure inspection launcher
#
# Usage:
#   ./launch_inspection.sh [OPTIONS]
#
# Options:
#   -s | --scenario <name>   Scenario name (default: pipeline_survey)
#                            Must match scenarios/<name>.toml
#   -w | --warp <n>          Time warp factor (default: 1)
#   -c | --clean             Delete previous run directory before generating
#   -h | --help              Show this message

SCENARIO="pipeline_survey"
WARP=1
CLEAN="no"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

SHORT=s:,w:,c,h
LONG=scenario:,warp:,clean,help
OPTS=$(getopt --options $SHORT --longoptions $LONG -- "$@")
if [ $? != 0 ]; then echo "Terminating..." >&2; exit 1; fi
eval set -- "$OPTS"

while true; do
  case "$1" in
    -s | --scenario ) SCENARIO=$2; shift 2 ;;
    -w | --warp )     WARP=$2;     shift 2 ;;
    -c | --clean )    CLEAN="yes"; shift   ;;
    -h | --help )
      echo "Usage: ./launch_inspection.sh [--scenario NAME] [--warp N] [--clean]"
      echo ""
      echo "Available scenarios:"
      ls "${SCRIPT_DIR}/scenarios/" | sed 's/\.toml//' | sed 's/^/  /'
      exit 0 ;;
    -- ) shift; break ;;
    *  ) echo "Unexpected option: $1"; break ;;
  esac
done

SCENARIO_FILE="${SCRIPT_DIR}/scenarios/${SCENARIO}.toml"
RUN_DIR="${SCRIPT_DIR}/run/${SCENARIO}"

if [ ! -f "$SCENARIO_FILE" ]; then
  echo "ERROR: Scenario file not found: $SCENARIO_FILE"
  echo "Available scenarios:"
  ls "${SCRIPT_DIR}/scenarios/" | sed 's/\.toml//' | sed 's/^/  /'
  exit 1
fi

if [ "$CLEAN" = "yes" ] && [ -d "$RUN_DIR" ]; then
  echo "Cleaning previous run directory: $RUN_DIR"
  rm -rf "$RUN_DIR"
fi

echo "Generating mission files for scenario: $SCENARIO"
python3 "${SCRIPT_DIR}/gen_inspection.py" \
  --scenario "$SCENARIO_FILE" \
  --outdir   "$RUN_DIR"

echo ""
echo "Generating mission briefing..."
python3 "${SCRIPT_DIR}/../../briefing/gen_briefing.py" \
  --scenario "$SCENARIO_FILE" \
  --output   "${RUN_DIR}/briefing.png" \
  --no-show  2>/dev/null \
  || echo "  (briefing graphic skipped — pip install matplotlib to enable)"

echo ""
echo "Launching with TIME_WARP=$WARP"
echo "  Run directory: $RUN_DIR"
echo ""
cd "$RUN_DIR"
exec ./launch.sh "$WARP"
