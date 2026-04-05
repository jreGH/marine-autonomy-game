# Serious Mission Options

This document describes the realistic maritime mission scenarios available on
the BWSI AUVC platform.  Each scenario is grounded in real-world AUV
operations and uses MOOS-IvP tools that are directly deployable on physical
vehicles.

| Scenario | Status | Mission directory |
|----------|--------|-------------------|
| A — GPS-Denied Acoustic Navigation | **Implemented** | `missions/gps_denied/` |
| B — Mine Countermeasures (MCM) | Reference only | — |
| C — Undersea Infrastructure Inspection | **Implemented** | `missions/inspection/` |

---

## Scenario A — GPS-Denied Acoustic Navigation

### Real-World Context

Underwater vehicles cannot receive GPS signals while submerged.  On long
dives, dead-reckoning navigation accumulates error.  Real AUVs (e.g., the
MIT/WHOI Bluefin Odyssey and REMUS vehicles) manage this by surfacing
periodically for a GPS fix, or by ranging to fixed acoustic beacons
(LBL — Long Baseline positioning).

This scenario teaches students how to design an autonomy policy that balances
**mission progress** (staying submerged to search) against **navigation
integrity** (surfacing to reduce position uncertainty).  Students also
implement trilateration — computing a position estimate from ≥3 beacon
range measurements.

### Launch

```bash
cd missions/gps_denied
./launch_gps_denied.sh --scenario beacon_nav --warp 4

# In a second terminal, after shoreside starts:
python student/examples/beacon_nav.py --vehicle jellyfish --port 9000
```

### MOOS-IvP Architecture

```
Shoreside community
  uFldBeaconRangeSensor  ← knows beacon positions; publishes range reports
  uFldShoreBroker        ← bridges BEACON_RANGE_REPORT to each vehicle

Vehicle community
  BHV_PeriodicSurface    ← forces ascent every surface_period seconds
  BHV_ConstantDepth      ← holds search depth while submerged
  BHV_Waypoint           ← executes lawnmower survey pattern
  student script         ← reads ranges, trilaterates, drives helm
```

### Key MOOS Variables

| Variable | Direction | Meaning |
|----------|-----------|---------|
| `BEACON_RANGE_REPORT` | sensor → vehicle | `label=beacon_01,dist=42.3` |
| `VEHICLE_AT_SURFACE` | behavior → student | `true` while BHV_PeriodicSurface has control |
| `DEPLOY` | shoreside → vehicle | Master on/off |
| `WPT_UPDATE` | student → helm | Update waypoint list: `points=x,y:x,y:...` |
| `DEPTH_UPDATES` | student → helm | Override dive depth: `depth=15.0` |
| `GPS_FIX_EVENT` | student → shoreside | Posted at each surface event for scoring |

### Sensor Model (uFldBeaconRangeSensor config)

| Parameter | Default | Effect |
|-----------|---------|--------|
| `default_beacon_push_dist` | 120 m | Beacon broadcasts within this range |
| `default_beacon_freq` | 0.2 Hz | One range measurement every 5 s |
| `rn_uniform_magnitude` | 2.0 m | Uniform range noise (±N metres) |

### Trilateration (student implementation)

The student script receives `BEACON_RANGE_REPORT` messages and estimates
position from ≥3 simultaneous measurements.  `beacon_nav.py` provides
two implementations:

```python
# Full nonlinear solver (requires scipy)
from student.examples.beacon_nav import trilaterate_scipy

# Algebraic closed-form (no external deps)
from student.examples.beacon_nav import trilaterate_algebraic
```

The algebraic method converts three circle equations to a linear system
by subtracting pairs:
```
2(x₂−x₁)x + 2(y₂−y₁)y = r₁²−r₂² + x₂²−x₁² + y₂²−y₁²
2(x₃−x₁)x + 2(y₃−y₁)y = r₁²−r₃² + x₃²−x₁² + y₃²−y₁²
```
Solving gives a closed-form (x, y) estimate with no iteration.

### Scoring

| Component | Basis |
|-----------|-------|
| Area coverage | Fraction of search box visited within `coverage_radius` |
| GPS fixes | `gps_fix_score` per successful surface event |
| Navigation quality | RMS error between acoustic estimate and true position at each fix (displayed in pMarineViewer) |

### Learning Objectives

- Trade-off between mission efficiency and navigation safety
- Acoustic ranging geometry (beacon placement determines fix quality)
- Implementing trilateration: algebraic vs. iterative methods
- Composing `BHV_PeriodicSurface` with a waypoint coverage pattern

---

## Scenario B — Mine Countermeasures (MCM)

*(Reference design — not yet implemented as a BWSI mission.)*

### Real-World Context

MCM is one of the primary operational uses of AUVs in navies worldwide.
The typical workflow is a two-stage search: a fast area-coverage pass with a
side-scan sonar to find Mine-Like Objects (MLOs), followed by a slower
re-investigation pass to classify each MLO as mine or benign.
Multi-vehicle teams split these roles to reduce total mission time.

Sensor data is inherently uncertain: real sonars have a **probability of
detection** (P_D < 1.0) and a **probability of false alarm** (P_FA > 0).

### MOOS-IvP Implementation

This scenario is fully supported by the existing **uField Toolbox** — no new
C++ code is needed.

**Key applications:**

| App | Role |
|-----|------|
| `uFldHazardSensor` | Places hazards; returns detections drawn from a P_D / P_FA ROC curve |
| `uFldHazardMgr` | Vehicle-side hazard map management and final mission report |
| `uFldHazardMetric` | Grades the final report against ground truth |

**Sensor config example:**
```
ProcessConfig = uFldHazardSensor
{
    sensor_config = width=25, exp=4, class=0.93, pd=0.9
}
```

**Key MOOS variables:**

| Variable | Direction | Meaning |
|----------|-----------|---------|
| `UHZ_SENSOR_REQUEST` | vehicle → sensor | Request a sweep at current position |
| `UHZ_DETECTION_REPORT` | sensor → vehicle | Raw detection: `x=...,y=...,label=<id>` |
| `UHZ_CLASSIFY_REPORT` | sensor → vehicle | Classification: `label=<id>,type=hazard\|benign` |

### Learning Objectives

- Sensor uncertainty and ROC trade-offs
- Multi-vehicle task allocation (search vs. classify)
- Reporting under time pressure with incomplete information

---

## Scenario C — Undersea Infrastructure Inspection

### Real-World Context

There are over 1.3 million km of submarine telecommunications cables and
extensive undersea gas and oil pipelines globally.  Periodic inspection is
required for integrity monitoring — detecting corrosion, anchor strikes,
fishing-gear entanglement, and free-span sections.  AUVs are increasingly
used for these surveys (e.g., Equinor / Saipem operations in the North Sea).

Unlike open-area search, infrastructure inspection has a strong geometric
constraint: the vehicle must survey a **linear corridor** and identify
discrete **anomaly points** along it.  This scenario is original work in
this course.

### Launch

```bash
cd missions/inspection
./launch_inspection.sh --scenario pipeline_survey --warp 4

# In a second terminal, after shoreside starts:
python student/examples/pipeline_survey.py --vehicle jellyfish --port 9000
```

### MOOS-IvP Architecture

```
Shoreside community
  pInfrastructureSensor  ← knows ground-truth pipeline geometry + anomalies
                            simulates forward-looking sonar on each vehicle
                            publishes INFRASTRUCTURE_DETECT_<VNAME>

  pInspectionScorer      ← tracks per-team coverage fraction
                            grades ANOMALY_REPORT_<VNAME> vs. ground truth
                            publishes INSPECTION_SCORE

  uFldShoreBroker        ← bridges detect messages to vehicle communities

Vehicle community
  BHV_Waypoint           ← lawnmower survey pattern
  BHV_Loiter             ← dwell / patrol
  student script         ← receives detections, clusters, reports anomalies
```

### pInfrastructureSensor

Configured in `shoreside.moos` (generated from the scenario TOML):

```
ProcessConfig = pInfrastructureSensor
{
  AppTick   = 4
  CommsTick = 4

  pipeline = label=cable_01,depth=30.0,
             points=-300,-80:-200,-130:-100,-180:0,-220:100,-200

  anomaly  = pipeline=cable_01,x=-100,y=-180,type=damage
  anomaly  = pipeline=cable_01,x=60,y=-210,type=corrosion

  detect_range  = 30.0    // max sensor range (m)
  detect_cone   = 60.0    // half-angle of forward detection cone (deg)
  noise_sigma   = 3.0     // position noise on detection reports (m σ)
  p_false_alarm = 0.02    // false alarm rate per vehicle per second
  reveal_pipe   = false   // if true, show full pipeline in viewer immediately
}
```

On startup, `pInfrastructureSensor` always publishes `VIEW_SEGLIST` for all
pipelines to the shoreside pMarineViewer (so instructors see the full route),
regardless of `reveal_pipe`.

**Sensor model per iteration:**
- For each vehicle, find the closest point on each pipeline segment
- If within `detect_range` AND within forward `detect_cone`: stochastic
  detection (P_D = 1 − range/detect_range, linear falloff)
- Anomalies: P_D boosted; each anomaly reported at most once per vehicle
- False alarms: Poisson-rate clutter at `p_false_alarm`/veh/s
- Position noise: Gaussian with σ = `noise_sigma`

### Key MOOS Variables

| Variable | Direction | Meaning |
|----------|-----------|---------|
| `INFRASTRUCTURE_DETECT_<VNAME>` | sensor → vehicle | `pipeline=cable_01,x=-102.3,y=-198.7,depth=30.0,type=pipe,range=22.4` |
| `INFRASTRUCTURE_DETECT_<VNAME>` | sensor → vehicle | `...,type=anomaly,anomaly_type=damage,range=8.1` |
| `ANOMALY_REPORT_<VNAME>` | student → shoreside | `pipeline=cable_01,x=-100.5,y=-179.2,type=anomaly,anomaly_type=damage,count=5` |
| `INSPECTION_SCORE` | scorer → shoreside | `team=alpha,score=1420,coverage=0.72,anomalies=2,fa=1\|team=bravo,...` |
| `VIEW_SEGLIST` | sensor → viewer | Pipeline outline (posted on startup + on first detection per vehicle) |
| `VIEW_POINT` | sensor/scorer → viewer | Anomaly marker (orange on detection; green on confirmed report) |

### pInspectionScorer

Also configured in `shoreside.moos` with the same `pipeline=` and `anomaly=`
lines as `pInfrastructureSensor`:

```
ProcessConfig = pInspectionScorer
{
  AppTick   = 4
  CommsTick = 4

  // (same pipeline= and anomaly= lines as pInfrastructureSensor)

  coverage_radius     = 30.0    // matches sensor detect_range
  coverage_score      = 1000    // max points for 100% coverage
  coverage_threshold  = 0.8     // fraction at which full score is awarded
  anomaly_score       = 500     // points per correctly identified anomaly
  false_alarm_penalty = 100     // points deducted per false positive
  report_tolerance    = 15.0    // match radius for anomaly reports (m)
  sample_step         = 5.0     // coverage grid resolution (m)
}
```

**Coverage algorithm:** The scorer samples each pipeline at 5 m intervals
and marks a sample as covered when any team vehicle passes within
`coverage_radius` metres.  Coverage fraction = covered/total.

**Anomaly grading:** When `ANOMALY_REPORT_<VNAME>` arrives, the scorer
finds the nearest ground-truth anomaly.  If within `report_tolerance`, it
is a true positive (claimed once per team); otherwise a false alarm.

### Student Script Pattern

The `pipeline_survey.py` example demonstrates the full workflow:

```python
# 1. Subscribe to detections
api._comms.register("INFRASTRUCTURE_DETECT", 0)

# 2. Cluster spatially — nearby detections = same feature
clusters = cluster_detections(detections["cable_01"])

# 3. Report confident clusters as anomalies
for cl in clusters:
    if cl["count"] >= MIN_CLUSTER_SIZE:
        api.notify("ANOMALY_REPORT_JELLYFISH",
                   f"pipeline={cl['pipeline']},x={cl['x']:.1f},"
                   f"y={cl['y']:.1f},type={cl['type']},"
                   f"anomaly_type={cl['anomaly_type']}")
```

### Scoring

| Component | Points |
|-----------|--------|
| Coverage (≥80% of pipeline) | up to 1000 |
| Per correctly located anomaly | 500 |
| Per false-alarm report | −100 |

### Learning Objectives

- Linear feature survey design (corridor width, along-track resolution)
- Sensor noise and detection clustering
- Real-time anomaly reporting workflow
- Trade-off between survey completeness and false alarm rate

---

## Comparison Table

| | Scenario A: GPS-Denied | Scenario B: MCM | Scenario C: Infrastructure Inspection |
|---|---|---|---|
| **Status** | Implemented | Reference only | Implemented |
| **Real-world domain** | AUV navigation | Naval mine warfare | Energy / telecoms |
| **Primary challenge** | Navigation uncertainty | Sensor uncertainty | Linear corridor tracking |
| **Multi-vehicle?** | Optional | Yes (search + classify) | Optional (parallel corridors) |
| **New C++ needed** | None | None | `pInfrastructureSensor`, `pInspectionScorer` |
| **Python example** | `beacon_nav.py` | — | `pipeline_survey.py` |
| **Difficulty** | Intermediate | Advanced | Intermediate–Advanced |
| **MOOS-IvP precedent** | Mission Delta | uFldHazardSensor | None — original work |

---

## References

All MOOS-IvP application behaviour and variable names cited here are drawn
from the official MOOS-IvP documentation:

- `uFldBeaconRangeSensor`, `BHV_PeriodicSurface`, GPS-denied navigation:
  *Mission Delta* — MOOS-IvP Lab documentation
- `uFldHazardSensor`, `uFldHazardMetric`, ROC curves, P_D / P_FA:
  *uField Toolbox* — MOOS-IvP Application Manual
- Pipeline / cable inspection: no existing MOOS-IvP precedent;
  `pInfrastructureSensor` and `pInspectionScorer` are original to this course

Additional background:
- P. M. Newman, "MOOS — Mission Oriented Operating Suite," MIT Tech Report, 2008
- M. Benjamin et al., "MOOS-IvP and a Mission Autonomy Protocol," *IFAC*, 2010
- A. Bahr et al., "Consistent Cooperative Localization," *ICRA*, 2009
  (motivation for GPS-denied beacon ranging)
