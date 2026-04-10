"""
pipeline_survey.py — BWSI AUVC infrastructure inspection example
================================================================

Strategy: lawnmower survey pattern over the arena, logging all
pInfrastructureSensor detections along the way.  Anomaly candidates
are tracked with a Bayesian belief state (DetectionBuffer) — only report
when the posterior probability exceeds a confidence threshold.

Run (from the student/ directory) after launching the mission:
    python examples/pipeline_survey.py --vehicle jellyfish --port 9000

Concepts demonstrated:
  - Receiving INFRASTRUCTURE_DETECT messages via VehicleAPI
  - Using DetectionBuffer for Bayesian log-odds belief tracking
  - Weighting observations by the 'confidence' (P_D) field in each message
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

from api import VehicleAPI, DetectionBuffer

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

# Bayesian belief parameters
PD_DEFAULT        = 0.7   # assumed P(detect | anomaly present)
PFA_DEFAULT       = 0.02  # assumed P(detect | no anomaly)
BELIEF_DECAY      = 0.99  # decay per loop iteration when no new data
REPORT_THRESHOLD  = 0.85  # report anomaly when P(present) >= this

# Count-based fallback: still report if cluster has this many raw detections
# even if Bayesian threshold not yet reached (guards against misconfigured PD)
MIN_CLUSTER_SIZE  = 5

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
        self.pipeline     = fields.get("pipeline", "")
        self.x            = float(fields.get("x", 0))
        self.y            = float(fields.get("y", 0))
        self.depth        = float(fields.get("depth", 0))
        self.type         = fields.get("type", "pipe")  # pipe|anomaly|false_alarm
        self.anomaly_type = fields.get("anomaly_type", "")
        self.range        = float(fields.get("range", 0))
        # confidence = P_D value used for this detection (from sensor model)
        self.confidence   = float(fields.get("confidence", PD_DEFAULT))

    def __repr__(self):
        return (f"Detection(pipeline={self.pipeline!r}, type={self.type!r}, "
                f"x={self.x:.1f}, y={self.y:.1f}, "
                f"range={self.range:.1f}, conf={self.confidence:.2f})")


# ---------------------------------------------------------------------------
# Cluster with Bayesian belief tracking
# ---------------------------------------------------------------------------

class Cluster:
    """
    Spatially-grouped detections with an attached DetectionBuffer.

    Each new detection within CLUSTER_RADIUS updates the belief state
    using the detection's own confidence (P_D) value from the sensor model.
    """

    def __init__(self, det: Detection):
        self.x            = det.x
        self.y            = det.y
        self.pipeline     = det.pipeline
        self.type         = det.type          # best guess at type so far
        self.anomaly_type = det.anomaly_type
        self.count        = 1
        self._belief      = DetectionBuffer(pd=PD_DEFAULT, pfa=PFA_DEFAULT,
                                            decay=BELIEF_DECAY)
        # First detection: update with its own confidence as P_D
        if det.type != "false_alarm":
            self._belief.update_positive(pd=det.confidence, pfa=PFA_DEFAULT)

    def add(self, det: Detection) -> None:
        """Merge a new detection into this cluster and update the belief."""
        n = self.count
        # Update centroid (running mean)
        self.x = (self.x * n + det.x) / (n + 1)
        self.y = (self.y * n + det.y) / (n + 1)
        self.count += 1

        if det.anomaly_type:
            self.anomaly_type = det.anomaly_type
        if det.type == "anomaly":
            self.type = "anomaly"

        # Bayesian update: weight by per-detection confidence (P_D)
        if det.type == "false_alarm":
            # A known false-alarm detection is a positive observation of
            # nothing useful — treat as null (slightly negative evidence)
            self._belief.update_negative(pd=PD_DEFAULT, pfa=PFA_DEFAULT)
        else:
            self._belief.update_positive(pd=det.confidence, pfa=PFA_DEFAULT)

    def tick_decay(self) -> None:
        self._belief.tick_decay()

    def probability(self) -> float:
        return self._belief.probability()

    def confirmed(self) -> bool:
        """True when Bayesian posterior or raw count exceeds threshold."""
        return (self._belief.decision(REPORT_THRESHOLD) or
                self.count >= MIN_CLUSTER_SIZE)


def find_or_create_cluster(clusters: List[Cluster], det: Detection) -> None:
    """Insert a detection into the nearest cluster, or create a new one."""
    for cl in clusters:
        if cl.pipeline != det.pipeline:
            continue
        dx = det.x - cl.x
        dy = det.y - cl.y
        if math.sqrt(dx*dx + dy*dy) < CLUSTER_RADIUS:
            cl.add(det)
            return
    clusters.append(Cluster(det))


# ---------------------------------------------------------------------------
# Mission
# ---------------------------------------------------------------------------

def run(vehicle_name: str, port: int, host: str):
    print(f"Connecting to vehicle '{vehicle_name}' at {host}:{port} …")

    api = VehicleAPI(vehicle_name, server_port=port, server_host=host)
    api.subscribe("INFRASTRUCTURE_DETECT")
    api.start(timeout=15.0)

    clusters: List[Cluster] = []
    reported: set            = set()   # cluster centroids already reported

    print("Connected.  Waiting for DEPLOY=true …")
    while not api.deployed:
        time.sleep(0.1)

    print("Mission started — beginning survey.")
    api.go_to_sequence(SURVEY_LEGS, speed=SURVEY_SPEED)

    last_status = time.time()
    n_raw_detections = 0

    while api.running:
        # ---- Drain incoming INFRASTRUCTURE_DETECT messages ----
        for msg in api.pop_messages("INFRASTRUCTURE_DETECT"):
            det = Detection(msg.string())
            if det.pipeline:
                find_or_create_cluster(clusters, det)
                n_raw_detections += 1

        # ---- Decay beliefs for clusters that received no new data ----
        for cl in clusters:
            cl.tick_decay()

        # ---- Check for confirmed anomalies and report ----
        vname_upper = vehicle_name.upper()
        for cl in clusters:
            if not cl.confirmed():
                continue
            if cl.type not in ("anomaly", "pipe"):
                continue  # skip pure false-alarm clusters

            key = (round(cl.x), round(cl.y))
            if key in reported:
                continue

            reported.add(key)
            report = (
                f"pipeline={cl.pipeline},"
                f"x={cl.x:.1f},"
                f"y={cl.y:.1f},"
                f"type={cl.type},"
                f"anomaly_type={cl.anomaly_type},"
                f"count={cl.count}"
            )
            api.notify(f"ANOMALY_REPORT_{vname_upper}", report)
            print(f"  REPORTED (P={cl.probability():.2f}): {report}")

        # ---- Status line ----
        if time.time() - last_status > STATUS_INTERVAL:
            confirmed_count = sum(1 for cl in clusters if cl.confirmed())
            print(f"  pos=({api.x:.0f},{api.y:.0f})  "
                  f"raw_detections={n_raw_detections}  "
                  f"clusters={len(clusters)}  "
                  f"confirmed={confirmed_count}  "
                  f"reported={len(reported)}")
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
