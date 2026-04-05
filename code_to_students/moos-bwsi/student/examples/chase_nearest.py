"""
chase_nearest.py — BWSI AUVC example student mission
=====================================================

Strategy: chase the nearest uncollected NPC contact.
  - Treasure scores highest → prioritise it.
  - Whale next, then fish.
  - Ignore sharks (getting bitten loses time).
  - When no target is in range, loiter in place.

Usage (from the student/ directory):
    python examples/chase_nearest.py --vehicle jellyfish --port 9000

The mission must already be running before you start this script.
If your scenario file has  student_mode = "python"  the generated .moos
file will not start pChallenge, so this script is the only decision-maker.
"""

import argparse
import sys
import time
from pathlib import Path

# Allow running from the student/ directory or from the repo root.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from api import VehicleAPI

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# How close (metres) before a contact counts as "collected".
COLLECT_DIST = 7.0

# Start chasing when a priority target is within this range.
MAX_CHASE_DIST = 60.0

# Update loop period in seconds (real time, not warped time).
LOOP_PERIOD = 0.25

# Priority map — higher is more desirable.
PRIORITY = {
    "treasure": 4,
    "whale":    3,
    "fish":     2,
    "shark":    -1,   # avoid — negative means skip
}


# ---------------------------------------------------------------------------
# Helper: pick the best target
# ---------------------------------------------------------------------------

def pick_target(api: VehicleAPI):
    """
    Return the highest-priority uncollected NPC contact within MAX_CHASE_DIST,
    or None if there are none.
    """
    best       = None
    best_score = (-999, float("inf"))   # (priority, distance) — higher priority first, then nearest

    for c in api.uncollected_contacts():
        if c.group != "npc":
            continue   # ignore other player vehicles

        priority = PRIORITY.get(c.type.lower(), 0)
        if priority < 0:
            continue   # skip sharks

        dist = c.distance_2d(api.x, api.y)
        if dist > MAX_CHASE_DIST:
            continue

        score = (priority, -dist)   # higher priority + closer → larger score
        if score > best_score:
            best_score = score
            best       = c

    return best


# ---------------------------------------------------------------------------
# Main mission loop
# ---------------------------------------------------------------------------

def run(vehicle_name: str, port: int, host: str, start_x: float, start_y: float):
    print(f"Connecting to vehicle '{vehicle_name}' at {host}:{port} …")
    api = VehicleAPI(vehicle_name, server_port=port, server_host=host,
                     start_x=start_x, start_y=start_y)
    api.start(timeout=15.0)
    print("Connected.  Waiting for DEPLOY=true …")

    # Wait for the mission to start.
    while not api.deployed:
        time.sleep(0.1)

    print("Mission started — entering control loop.")

    while api.running:
        target = pick_target(api)

        if target is None:
            # Nothing in range — hold position.
            api.loiter()
        else:
            dist = target.distance_2d(api.x, api.y)
            if dist < COLLECT_DIST:
                print(f"  Collected: {target.name} ({target.type}) at dist={dist:.1f}m")
                api.mark_collected(target)
                api.loiter()
            else:
                api.chase(target.name)

        api.sleep(LOOP_PERIOD)

    print("Mission ended (DEPLOY=false or connection lost).")
    api.stop()


# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Chase-nearest student mission")
    parser.add_argument("--vehicle", default="jellyfish",
                        help="Vehicle community name (default: jellyfish)")
    parser.add_argument("--port", type=int, default=9000,
                        help="MOOSDB port for this vehicle (default: 9000)")
    parser.add_argument("--host", default="localhost",
                        help="Host running MOOSDB (default: localhost)")
    parser.add_argument("--start-x", type=float, default=0.0)
    parser.add_argument("--start-y", type=float, default=-175.0)
    args = parser.parse_args()

    run(args.vehicle, args.port, args.host, args.start_x, args.start_y)


if __name__ == "__main__":
    main()
