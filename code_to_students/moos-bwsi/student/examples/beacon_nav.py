"""
beacon_nav.py — BWSI AUVC GPS-denied navigation example
========================================================

Demonstrates:
  1. Receiving BEACON_RANGE_REPORT from uFldBeaconRangeSensor.
  2. Simple trilateration from ≥3 range measurements to estimate
     position when GPS is unavailable (while submerged).
  3. Detecting the VEHICLE_AT_SURFACE flag to know when GPS is
     valid and resetting the dead-reckoning estimate.
  4. Executing a lawnmower survey of the search box.

Background — acoustic positioning
----------------------------------
While submerged, NAV_X/NAV_Y from uSimMarine is still "perfect"
in simulation (the sim doesn't degrade navigation).  Real hardware
would replace those with dead-reckoning.  This script IGNORES the
sim's NAV_X/NAV_Y while submerged and estimates position from
beacon ranges instead, so students practice the algorithm that
would run on real hardware.

Trilateration algorithm
-----------------------
Given n ≥ 3 beacons at known positions (bx_i, by_i) with measured
ranges r_i, find (x, y) that minimises:

    Σ  (sqrt((x-bx_i)² + (y-by_i)²) - r_i)²

We use a simple gradient-free least-squares approach (Levenberg–
Marquardt via scipy.optimize.least_squares).  If scipy is not
available, we fall back to an algebraic closed-form from pairs.

Run after launching the mission:
    python examples/beacon_nav.py --vehicle jellyfish --port 9000
"""

import argparse
import math
import sys
import time
from collections import deque
from pathlib import Path
from typing import Dict, List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from api import VehicleAPI

# ---------------------------------------------------------------------------
# Try to import scipy for LM solver; fall back to algebraic if absent
# ---------------------------------------------------------------------------
try:
    from scipy.optimize import least_squares as _scipy_ls
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False
    print("Note: scipy not found — using algebraic trilateration fallback.")

# ---------------------------------------------------------------------------
# Known beacon positions (must match scenario TOML)
# ---------------------------------------------------------------------------
BEACONS: Dict[str, Tuple[float, float]] = {
    "beacon_01": (-180.0, -180.0),
    "beacon_02": ( 180.0, -180.0),
    "beacon_03": (   0.0, -390.0),
}

# ---------------------------------------------------------------------------
# Survey pattern — a lawnmower over the search box
# ---------------------------------------------------------------------------
SURVEY_LEGS: List[Tuple[float, float]] = [
    (-190, -160), (-190, -390),
    (-130, -390), (-130, -160),
    ( -70, -160), ( -70, -390),
    (  -0, -390), (  -0, -160),
    (  70, -160), (  70, -390),
    ( 130, -390), ( 130, -160),
    ( 190, -160), ( 190, -390),
]
SURVEY_SPEED = 1.5  # m/s
LOOP_PERIOD  = 0.25


# ---------------------------------------------------------------------------
# Trilateration
# ---------------------------------------------------------------------------

def _residuals(pos, beacons_xy, ranges):
    """Residuals for least-squares: (estimated_range - measured_range) per beacon."""
    x, y = pos
    res = []
    for (bx, by), r in zip(beacons_xy, ranges):
        estimated = math.sqrt((x - bx)**2 + (y - by)**2)
        res.append(estimated - r)
    return res


def trilaterate_scipy(measurements: Dict[str, float],
                      initial: Tuple[float, float]) -> Optional[Tuple[float, float]]:
    """Levenberg–Marquardt trilateration using scipy."""
    valid = [(BEACONS[k], v) for k, v in measurements.items()
             if k in BEACONS and v > 0]
    if len(valid) < 2:
        return None
    beacons_xy = [b for b, _ in valid]
    ranges     = [r for _, r in valid]
    result = _scipy_ls(_residuals, x0=list(initial),
                       args=(beacons_xy, ranges),
                       method='lm')
    if result.success:
        return (result.x[0], result.x[1])
    return None


def trilaterate_algebraic(measurements: Dict[str, float],
                           initial: Tuple[float, float]) -> Optional[Tuple[float, float]]:
    """
    Algebraic closed-form for exactly 3 beacons.
    Converts range equations to a linear system by subtracting pairs.
    Falls back to centroid-weighted-by-range if geometry is degenerate.
    """
    valid = [(BEACONS[k], v) for k, v in measurements.items()
             if k in BEACONS and v > 0]
    if len(valid) < 2:
        return None
    if len(valid) == 2:
        # With only 2 beacons, return point on the line between them
        # at the correct ranges (approximate).
        (b1x, b1y), r1 = valid[0]
        (b2x, b2y), r2 = valid[1]
        t = r1 / (r1 + r2)
        return (b1x + t*(b2x - b1x), b1y + t*(b2y - b1y))

    # Use first 3 beacons; convert circles to linear system
    (x1, y1), r1 = valid[0]
    (x2, y2), r2 = valid[1]
    (x3, y3), r3 = valid[2]

    # Subtracting circle equations: 2(x2-x1)x + 2(y2-y1)y = r1²-r2²+x2²-x1²+y2²-y1²
    A = [[2*(x2-x1), 2*(y2-y1)],
         [2*(x3-x1), 2*(y3-y1)]]
    b = [r1**2 - r2**2 + x2**2 - x1**2 + y2**2 - y1**2,
         r1**2 - r3**2 + x3**2 - x1**2 + y3**2 - y1**2]

    det = A[0][0]*A[1][1] - A[0][1]*A[1][0]
    if abs(det) < 1e-6:
        return initial   # Degenerate — beacons are colinear

    x = (b[0]*A[1][1] - b[1]*A[0][1]) / det
    y = (A[0][0]*b[1] - A[1][0]*b[0]) / det
    return (x, y)


def estimate_position(measurements: Dict[str, float],
                      initial: Tuple[float, float]) -> Optional[Tuple[float, float]]:
    """Use best available trilateration method."""
    if HAS_SCIPY:
        return trilaterate_scipy(measurements, initial)
    return trilaterate_algebraic(measurements, initial)


# ---------------------------------------------------------------------------
# Custom VehicleAPI subclass — adds BEACON_RANGE_REPORT subscription
# ---------------------------------------------------------------------------

class GPSDeniedVehicle(VehicleAPI):
    """VehicleAPI extended with acoustic navigation state."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._at_surface      = False
        self._beacon_ranges   : Dict[str, float] = {}
        self._acoustic_pos    : Optional[Tuple[float, float]] = None
        self._pos_history     : deque = deque(maxlen=10)  # smoothing

    def _on_connect(self):
        super()._on_connect()
        self._comms.register("BEACON_RANGE_REPORT", 0)
        self._comms.register("VEHICLE_AT_SURFACE",  0)
        return True

    def _handle_messages(self, messages):
        super()._handle_messages(messages)
        with self._lock:
            for msg in messages:
                key = msg.key()
                if key == "BEACON_RANGE_REPORT":
                    # Format: "label=beacon_01,dist=42.3"
                    raw = msg.string()
                    label = _field(raw, "label")
                    dist  = _field(raw, "dist")
                    if label and dist:
                        self._beacon_ranges[label] = float(dist)
                elif key == "VEHICLE_AT_SURFACE":
                    self._at_surface = msg.string().strip().lower() == "true"

    @property
    def at_surface(self) -> bool:
        """True when BHV_PeriodicSurface has brought the vehicle to the surface."""
        with self._lock:
            return self._at_surface

    @property
    def beacon_ranges(self) -> Dict[str, float]:
        """Most recent range measurement from each beacon."""
        with self._lock:
            return dict(self._beacon_ranges)

    def update_acoustic_position(self) -> Optional[Tuple[float, float]]:
        """
        Run trilateration and update the acoustic position estimate.
        Returns the estimate, or None if insufficient data.
        """
        ranges  = self.beacon_ranges
        initial = self.position  # use last known position as starting guess
        pos = estimate_position(ranges, initial)
        if pos:
            with self._lock:
                self._pos_history.append(pos)
                if self._pos_history:
                    xs = [p[0] for p in self._pos_history]
                    ys = [p[1] for p in self._pos_history]
                    self._acoustic_pos = (sum(xs)/len(xs), sum(ys)/len(ys))
        return self._acoustic_pos

    @property
    def acoustic_position(self) -> Optional[Tuple[float, float]]:
        """Smoothed acoustic position estimate, or None."""
        with self._lock:
            return self._acoustic_pos


def _field(raw: str, key: str) -> str:
    for token in raw.split(","):
        if "=" in token:
            k, _, v = token.partition("=")
            if k.strip() == key:
                return v.strip()
    return ""


# ---------------------------------------------------------------------------
# Main mission loop
# ---------------------------------------------------------------------------

def run(vehicle_name: str, port: int, host: str, start_x: float, start_y: float):
    print(f"Connecting to '{vehicle_name}' at {host}:{port} …")

    api = GPSDeniedVehicle(vehicle_name, server_port=port, server_host=host,
                           start_x=start_x, start_y=start_y)
    api.start(timeout=15.0)
    print("Connected.  Waiting for DEPLOY=true …")

    while not api.deployed:
        time.sleep(0.1)

    print("Mission started.  Beginning lawnmower survey.")
    api.go_to_sequence(SURVEY_LEGS, speed=SURVEY_SPEED)

    last_status = time.time()
    prev_at_surface = False

    while api.running:
        # Update acoustic position estimate
        apos = api.update_acoustic_position()

        # Detect surface events — when vehicle surfaces, GPS is valid
        at_surf = api.at_surface
        if at_surf and not prev_at_surface:
            print(f"  [SURFACE] GPS fix valid. "
                  f"True pos: ({api.x:.1f}, {api.y:.1f})  "
                  f"Acoustic: {f'({apos[0]:.1f}, {apos[1]:.1f})' if apos else 'n/a'}  "
                  f"Error: {math.sqrt((api.x-apos[0])**2 + (api.y-apos[1])**2):.1f}m"
                  if apos else "  [SURFACE] GPS valid (no acoustic estimate yet)")
            # Clear position history so we restart from a clean GPS fix
            api._pos_history.clear()
            # Report GPS fix to shoreside (for scoring)
            api.notify("GPS_FIX_EVENT",
                       f"vehicle={vehicle_name},x={api.x:.1f},y={api.y:.1f}")
        prev_at_surface = at_surf

        # Status line
        if time.time() - last_status > 5.0:
            ranges_str = ", ".join(
                f"{k}={v:.1f}" for k, v in api.beacon_ranges.items())
            apos_str = (f"({apos[0]:.1f},{apos[1]:.1f})" if apos else "n/a")
            print(f"  pos=({api.x:.0f},{api.y:.0f})  "
                  f"acoustic={apos_str}  "
                  f"depth={api.depth:.1f}m  "
                  f"surface={'YES' if at_surf else 'no'}  "
                  f"ranges=[{ranges_str}]")
            last_status = time.time()

        api.sleep(LOOP_PERIOD)

    print("Mission ended.")
    api.stop()


# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="GPS-denied navigation example")
    parser.add_argument("--vehicle",  default="jellyfish")
    parser.add_argument("--port",     type=int, default=9000)
    parser.add_argument("--host",     default="localhost")
    parser.add_argument("--start-x",  type=float, default=-50.0)
    parser.add_argument("--start-y",  type=float, default=-120.0)
    args = parser.parse_args()

    run(args.vehicle, args.port, args.host, args.start_x, args.start_y)


if __name__ == "__main__":
    main()
