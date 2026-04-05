"""
pipeline_survey.py — BWSI AUVC infrastructure inspection example
================================================================

Strategy: lawnmower survey pattern over the arena, logging all
pInfrastructureSensor detections along the way.  When enough
detections have been collected, report anomaly positions to shoreside.

Run (from the student/ directory) after launching the mission:
    python examples/pipeline_survey.py --vehicle jellyfish --port 9000

Concepts demonstrated:
  - Receiving INFRASTRUCTURE_DETECT messages via VehicleAPI.notify
    (we must call api.notify_subscribe to add extra subscriptions)
  - Building a local detection map indexed by pipeline label
  - Reporting anomaly clusters back to shoreside via ANOMALY_REPORT
  - go_to_sequence() for a pre-planned survey route
"""

import argparse
import math
import sys
import time
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from api import VehicleAPI

# ---------------------------------------------------------------------------
# Tunable constants
# ---------------------------------------------------------------------------

# Lawnmower survey legs.  Adjust to match your scenario's arena.
# Format: [(x, y), ...]
SURVEY_LEGS = [
    (-300, -100),
    (-300, -480),
    (-200, -480),
    (-200, -100),
    (-100, -100),
    (-100, -480),
    (   0, -480),
    (   0, -100),
    ( 100, -100),
    ( 100, -480),
    ( 200, -480),
    ( 200, -100),
    ( 300, -100),
    ( 300, -480),
]

SURVEY_SPEED      = 1.8   # m/s
LOOP_PERIOD       = 0.25  # seconds between logic updates

# Cluster nearby detections: consider two detections the same anomaly if
# their reported positions are within this distance (m).
CLUSTER_RADIUS    = 15.0

# Minimum detections in a cluster before we report it as a confirmed anomaly.
MIN_CLUSTER_SIZE  = 3

# How often (s) to print a status line.
STATUS_INTERVAL   = 5.0


# ---------------------------------------------------------------------------
# Detection record
# ---------------------------------------------------------------------------

class Detection:
    """One parsed INFRASTRUCTURE_DETECT message."""

    def __init__(self, raw: str):
        fields = {}
        for token in raw.split(","):
            if "=" in token:
                k, _, v = token.partition("=")
                fields[k.strip()] = v.strip()
        self.pipeline    = fields.get("pipeline", "")
        self.x           = float(fields.get("x", 0))
        self.y           = float(fields.get("y", 0))
        self.depth       = float(fields.get("depth", 0))
        self.type        = fields.get("type", "pipe")   # pipe | anomaly | false_alarm
        self.anomaly_type = fields.get("anomaly_type", "")
        self.range       = float(fields.get("range", 0))

    def __repr__(self):
        return (f"Detection(pipeline={self.pipeline!r}, type={self.type!r}, "
                f"x={self.x:.1f}, y={self.y:.1f}, range={self.range:.1f})")


# ---------------------------------------------------------------------------
# Cluster analysis
# ---------------------------------------------------------------------------

def cluster_detections(detections: List[Detection]) -> List[Dict]:
    """
    Group detections spatially.  Returns a list of cluster dicts:
        { 'x': float, 'y': float, 'count': int,
          'type': str, 'anomaly_type': str, 'pipeline': str }
    """
    clusters = []

    for det in detections:
        placed = False
        for cl in clusters:
            dx = det.x - cl["x"]
            dy = det.y - cl["y"]
            if math.sqrt(dx*dx + dy*dy) < CLUSTER_RADIUS:
                # Update cluster centroid (running mean)
                n = cl["count"]
                cl["x"] = (cl["x"] * n + det.x) / (n + 1)
                cl["y"] = (cl["y"] * n + det.y) / (n + 1)
                cl["count"] += 1
                if det.anomaly_type:
                    cl["anomaly_type"] = det.anomaly_type
                placed = True
                break
        if not placed:
            clusters.append({
                "x": det.x, "y": det.y,
                "count": 1,
                "type": det.type,
                "anomaly_type": det.anomaly_type,
                "pipeline": det.pipeline,
            })

    return clusters


# ---------------------------------------------------------------------------
# Extended VehicleAPI with INFRASTRUCTURE_DETECT subscription
# OverridesAPI callbacks are not available directly, so we poll a raw
# MOOS variable via a custom pymoos subclass approach.  For this example
# we demonstrate the pattern using api.notify() for subscribing manually.
# ---------------------------------------------------------------------------

def run(vehicle_name: str, port: int, host: str):
    print(f"Connecting to vehicle '{vehicle_name}' at {host}:{port} …")

    # VehicleAPI.start() subscribes to standard nav variables.
    # We also need INFRASTRUCTURE_DETECT, which arrives as a string.
    # We achieve this by subclassing _on_connect — but to keep this example
    # readable without subclassing, we register it via the comms object
    # directly after start().
    api = VehicleAPI(vehicle_name, server_port=port, server_host=host)
    api.start(timeout=15.0)

    # Register the extra subscription we need
    api._comms.register("INFRASTRUCTURE_DETECT", 0)

    # Local detection store: pipeline_label → list of Detection
    detections: Dict[str, List[Detection]] = defaultdict(list)
    reported_clusters = set()   # cluster centroids already reported (x_int, y_int)

    print("Connected.  Waiting for DEPLOY=true …")
    while not api.deployed:
        time.sleep(0.1)

    print("Mission started — beginning survey.")

    # Start lawnmower pattern
    api.go_to_sequence(SURVEY_LEGS, speed=SURVEY_SPEED)

    last_status = time.time()
    n_detections = 0

    while api.running:
        # ---- Drain any queued INFRASTRUCTURE_DETECT messages ----
        # pymoos delivers mail via the on_new_mail callback (runs in the
        # VehicleAPI background thread).  We need to intercept it here.
        # Simplest approach for this example: poll via _comms.fetch().
        # In production, subclass VehicleAPI and override _on_new_mail.
        msgs = api._comms.fetch()
        for msg in msgs:
            if msg.key() == "INFRASTRUCTURE_DETECT":
                det = Detection(msg.string())
                if det.pipeline:
                    detections[det.pipeline].append(det)
                    n_detections += 1

        # ---- Cluster analysis & anomaly reporting ----
        for pipeline_label, dets in detections.items():
            clusters = cluster_detections(dets)
            for cl in clusters:
                if cl["count"] < MIN_CLUSTER_SIZE:
                    continue
                if cl["type"] not in ("anomaly", "pipe"):
                    continue  # skip false_alarm clusters

                key = (round(cl["x"]), round(cl["y"]))
                if key in reported_clusters:
                    continue

                reported_clusters.add(key)
                report = (
                    f"pipeline={cl['pipeline']},"
                    f"x={cl['x']:.1f},"
                    f"y={cl['y']:.1f},"
                    f"type={cl['type']},"
                    f"anomaly_type={cl['anomaly_type']},"
                    f"vehicle={vehicle_name},"
                    f"count={cl['count']}"
                )
                vname_upper = vehicle_name.upper()
                api.notify(f"ANOMALY_REPORT_{vname_upper}", report)
                print(f"  REPORTED: {report}")

        # ---- Status line ----
        if time.time() - last_status > STATUS_INTERVAL:
            total = sum(len(v) for v in detections.values())
            print(f"  pos=({api.x:.0f},{api.y:.0f})  "
                  f"detections={total}  "
                  f"clusters_reported={len(reported_clusters)}")
            last_status = time.time()

        api.sleep(LOOP_PERIOD)

    print("Mission ended.")
    api.stop()


# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Pipeline survey student mission")
    parser.add_argument("--vehicle", default="jellyfish")
    parser.add_argument("--port",    type=int, default=9000)
    parser.add_argument("--host",    default="localhost")
    args = parser.parse_args()

    run(args.vehicle, args.port, args.host)


if __name__ == "__main__":
    main()
