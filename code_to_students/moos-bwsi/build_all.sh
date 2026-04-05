#!/bin/bash -e
# Build the libBWSI shared library and all pChallenge_* apps.
# Run from the root of the moos-bwsi directory:
#   cd ~/moos-bwsi && ./build_all.sh
#
# Prerequisites: moos-ivp must be built and installed at ~/moos-ivp/

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=== Building libBWSI ==="
make -C "${SCRIPT_DIR}/lib/libBWSI"

echo ""
echo "=== Building pChallenge (student) ==="
make -C "${SCRIPT_DIR}/behaviors/pChallenge"

echo ""
echo "=== Building NPC apps ==="
make -C "${SCRIPT_DIR}/behaviors/pChallenge_shark"
make -C "${SCRIPT_DIR}/behaviors/pChallenge_fish"
make -C "${SCRIPT_DIR}/behaviors/pChallenge_whale"
make -C "${SCRIPT_DIR}/behaviors/pChallenge_treasure"

echo ""
echo "=== Building pChallenge_shoreside ==="
make -C "${SCRIPT_DIR}/behaviors/pChallenge_shoreside"

echo ""
echo "=== Building pInfrastructureSensor ==="
make -C "${SCRIPT_DIR}/behaviors/pInfrastructureSensor"

echo ""
echo "=== Building pInspectionScorer ==="
make -C "${SCRIPT_DIR}/behaviors/pInspectionScorer"

echo ""
echo "=== Build complete ==="
echo "Binaries installed to: ${HOME}/moos-bwsi/behaviors/bin"
