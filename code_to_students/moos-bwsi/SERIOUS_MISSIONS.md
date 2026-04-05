# Serious Mission Options

This document describes three realistic maritime mission scenarios that can be
run on the BWSI AUVC platform.  Each scenario is grounded in real-world AUV
operations and uses MOOS-IvP tools that are directly deployable on physical
vehicles.

Pipeline and cable inspection (Scenario C) is new work built for this course;
the other two scenarios draw on existing MOOS-IvP mission infrastructure.

---

## Scenario A — GPS-Denied Area Search

### Real-World Context

Underwater vehicles cannot receive GPS signals while submerged.  On long
dives, dead-reckoning navigation accumulates error.  Real AUVs (e.g., the
MIT/WHOI Bluefin Odyssey and REMUS vehicles) manage this by surfacing
periodically for a GPS fix, or by ranging to fixed acoustic beacons
(LBL — Long Baseline, or USBL — Ultra-Short Baseline positioning).

This scenario teaches students how to design an autonomy policy that balances
**mission progress** (staying submerged to search) against **navigation
integrity** (surfacing to reduce position uncertainty).

### MOOS-IvP Implementation

The scenario is documented as **Mission Delta** in the MOOS-IvP literature.

**Key applications:**

| App / Behavior | Role |
|---|---|
| `uFldBeaconRangeSensor` | Shoreside — simulates acoustic beacons at known positions, responds to vehicle range requests, publishes `VIEW_RANGE_PULSE` for GUI display |
| `BHV_PeriodicSurface` | Vehicle — forces the AUV to the surface at configurable intervals; resets when `GPS_UPDATE_RECEIVED` is posted |
| `BHV_Waypoint` (lawnmower) | Vehicle — executes the search pattern between surfacing events |
| `pBasicContactMgr` | Vehicle — tracks beacon ranges and fuses them into a position estimate |

**Key MOOS variables:**

| Variable | Direction | Meaning |
|---|---|---|
| `GPS_UPDATE_RECEIVED` | written by nav filter | Tells `BHV_PeriodicSurface` that a fix was obtained; resets the surfacing timer |
| `PENDING_SURFACE` | published by behavior | Countdown to mandatory next surface event |
| `VIEW_RANGE_PULSE` | published by sensor | Draws acoustic ping circles on the pMarineViewer map |

**Scoring:**
- Coverage fraction of the search polygon
- Navigation error at mission end (estimated vs. true position)
- Total time spent at surface (penalises over-surfacing)

### Learning Objectives

- Trade-off between mission efficiency and navigation safety
- Acoustic ranging geometry (beacon placement matters for fix quality)
- Composing `BHV_PeriodicSurface` with an area-coverage waypoint pattern

---

## Scenario B — Mine Countermeasures (MCM)

### Real-World Context

MCM is one of the primary operational uses of AUVs in navies worldwide.
The typical workflow is a two-stage search: a fast area-coverage pass with a
side-scan sonar to find Mine-Like Objects (MLOs), followed by a slower
re-investigation pass to classify each MLO as mine or benign.
Multi-vehicle teams split these roles to reduce total mission time.

Sensor data is inherently uncertain: real sonars have a **probability of
detection** (P_D < 1.0) and a **probability of false alarm** (P_FA > 0).
Mission planning must account for this.

### MOOS-IvP Implementation

This scenario is supported by the **uField Toolbox** hazard simulation suite.

**Key applications:**

| App / Behavior | Role |
|---|---|
| `uFldHazardSensor` | Shoreside — places hazards and benign objects in a field; responds to vehicle sensor requests; returns noisy detections drawn from a ROC curve parameterised by P_D and P_FA |
| `uFldHazardMgr` | Vehicle — manages incoming sensor reports, maintains a local hazard map, generates the final mission report to shore |
| `uFldHazardMetric` | Shoreside — grades the vehicle's hazard report against ground truth; computes false-alarm rate and missed-detection rate |
| `BHV_Waypoint` (lawnmower) | Vehicle — systematic area coverage for the search phase |
| `BHV_CutRange` | Vehicle — close on a specific MLO for re-investigation |

**Sensor model:**  
The sensor operates on a ROC curve — increasing P_D necessarily increases
P_FA.  Students configure their desired operating point in the `.moos` file:

```
ProcessConfig = uFldHazardSensor
{
    sensor_config = width=25, exp=4, class=0.93, pd=0.9
    //               ↑beam    ↑shape ↑classifier  ↑P_D at this config
}
```

**Key MOOS variables:**

| Variable | Direction | Meaning |
|---|---|---|
| `UHZ_SENSOR_REQUEST` | vehicle → sensor | Vehicle requests a sensor sweep at its current position |
| `UHZ_DETECTION_REPORT` | sensor → vehicle | Raw detection: `x=...,y=...,label=<id>` |
| `UHZ_CLASSIFY_REPORT` | sensor → vehicle | Classification result: `label=<id>,type=hazard\|benign` |
| `UHZ_MISSION_PARAMS` | shoreside → vehicle | Provides search polygon, time limit, and sensor config |

**Scoring (via `uFldHazardMetric`):**
- Missed-detection rate (undetected real mines)
- False-alarm rate (benign objects reported as mines)
- Time to mission completion

### Learning Objectives

- Sensor uncertainty and ROC trade-offs in operational planning
- Multi-vehicle task allocation (search vs. classify roles)
- Reporting under time pressure with incomplete information

---

## Scenario C — Undersea Infrastructure Inspection

### Real-World Context

There are over 1.3 million km of submarine telecommunications cables and
extensive undersea gas and oil pipelines globally.  Periodic inspection is
required for integrity monitoring — detecting corrosion, anchor strikes,
fishing gear entanglement, and free-span sections.  AUVs are increasingly
used for these surveys (e.g., Equinor / Saipem operations in the North Sea;
GEBCO Seabed 2030 mapping programmes).

Unlike open-area search, infrastructure inspection has a strong geometric
constraint: the vehicle must survey a **linear corridor** and identify
discrete **anomaly points** along it.

This scenario is **original work** in this course — there is no existing
MOOS-IvP mission for pipeline inspection — and forms a core part of the
serious-mode curriculum.

### MOOS-IvP Implementation (Planned)

The scenario is implemented using a custom shoreside application
(`pInfrastructureSensor`) alongside standard MOOS-IvP tools.

**Three-phase mission:**

```
Phase 1: Discovery
  Vehicle executes a lawnmower survey.
  pInfrastructureSensor fires a detection event when the vehicle
  passes within sonar range of the pipeline polyline (with noise).

Phase 2: Localization
  Detection points are reported to shore.
  pCorridorPlanner fits a corridor to detections and pushes updated
  BHV_Waypoint waypoints to the vehicle in real time.
  The pipeline appears on the pMarineViewer map as a VIEW_SEGLIST.

Phase 3: Pipe Crawl + Anomaly Survey
  Vehicle executes a tight track-line survey along the corridor.
  At anomaly locations, pInfrastructureSensor triggers a dwell event.
  The vehicle loiters (BHV_Loiter with center_assign update) for a
  configurable dwell time to "image" the anomaly.
```

**Applications to be built:**

| App | Role |
|---|---|
| `pInfrastructureSensor` | Shoreside — knows the pipeline geometry (polyline + anomaly positions); simulates forward-looking sonar detection range and noise |
| `pCorridorPlanner` | Shoreside — fits a best-estimate corridor to detection reports; publishes `WPT_UPDATE` with revised waypoints |

**Key MOOS variables (planned):**

| Variable | Direction | Meaning |
|---|---|---|
| `INFRA_DETECTION` | sensor → vehicle | Detection event: `x=...,y=...,confidence=0.8` |
| `INFRA_ANOMALY` | sensor → vehicle | Anomaly found at current position: `id=<n>,type=corrosion` |
| `INFRA_CORRIDOR` | planner → vehicle | Updated corridor polygon for `BHV_OpRegion` constraint |
| `WPT_UPDATE` | planner → vehicle | Revised waypoint list along confirmed pipeline route |

**Standard tools used:**

| Tool | Purpose |
|---|---|
| `BHV_Waypoint` (lawnmower format) | Discovery phase area coverage |
| `BHV_Waypoint` (track-line) | Pipe crawl along confirmed corridor |
| `BHV_Loiter` (polygon, `center_assign`) | Anomaly dwell — center moved to anomaly position at runtime |
| `pSearchGrid` | Coverage tracking — records vehicle positions in a grid over the search zone |

**Game-mode simplification:**
In game mode, the pipeline is visible on the map from mission start.  Students
navigate to it and execute the survey without the discovery phase.  Score is
based on fraction of the pipe corridor covered (from `pSearchGrid`) and number
of anomalies correctly identified.

**Scoring:**
- Corridor coverage fraction
- Anomalies detected vs. missed
- False anomaly reports
- Total mission time

### Learning Objectives

- Linear feature survey design (corridor width, along-track resolution)
- Real-time mission replanning from sensor detections
- Dynamic behavior parameter updates (`center_assign`, `WPT_UPDATE`)
- Trade-off between survey speed and detection completeness

---

## Comparison Table

| | Scenario A: GPS-Denied Search | Scenario B: MCM | Scenario C: Infrastructure Inspection |
|---|---|---|---|
| **Real-world domain** | General AUV navigation | Naval mine warfare | Energy / telecoms |
| **Primary challenge** | Navigation uncertainty | Sensor uncertainty | Linear feature tracking |
| **Multi-vehicle?** | Optional | Yes (search + classify) | Optional (parallel corridors) |
| **New code needed** | None (uses Mission Delta) | None (uses uFldHazardSensor) | Yes (`pInfrastructureSensor`, `pCorridorPlanner`) |
| **Difficulty** | Intermediate | Advanced | Advanced |
| **MOOS-IvP precedent** | Mission Delta | uFldHazardSensor suite | None — original work |

---

## References

All MOOS-IvP application behaviour and variable names cited here are drawn
from the official MOOS-IvP documentation collected in the course NotebookLM
reference ([notebook](https://notebooklm.google.com/notebook/2742f222-718d-4e31-af3c-3781e90381ea)):

- `uFldBeaconRangeSensor`, `BHV_PeriodicSurface`, GPS-denied navigation:
  *Mission Delta* — MOOS-IvP Lab documentation
- `uFldHazardSensor`, `uFldHazardMetric`, ROC curves, P_D / P_FA:
  *uField Toolbox* — MOOS-IvP Application Manual
- `pSearchGrid`, `CoverageMap`, EER metric:
  *Multi-AUV Seabed Coverage* — MOOS-IvP documentation
- Pipeline / cable inspection: no existing MOOS-IvP precedent;
  scenario design is original to this course

Additional background:
- P. M. Newman, "MOOS — Mission Oriented Operating Suite," MIT Tech Report, 2008
- M. Benjamin et al., "MOOS-IvP and a Mission Autonomy Protocol," *IFAC*, 2010
- A. Bahr et al., "Consistent Cooperative Localization," *ICRA*, 2009
  (motivation for GPS-denied beacon ranging)
