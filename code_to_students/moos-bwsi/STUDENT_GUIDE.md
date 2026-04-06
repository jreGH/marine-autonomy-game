# Student Behavior Development Guide

This guide explains how to program your vehicle's autonomy for the BWSI
AUVC challenge.  You do not need to understand all of MOOS-IvP to
compete — this document covers everything your code needs to know.

## Two programming tracks

| Track | Entry point | Language |
|-------|-------------|----------|
| **Python** (recommended for beginners) | `student/api/VehicleAPI.py` | Python 3 + pymoos |
| **C++** (recommended for full control) | `behaviors/pChallenge/Challenge.cpp` | C++ / MOOS-IvP |

Both tracks publish and subscribe to the same MOOS variables, so you can
start in Python and switch to C++ later without changing the scenario or
behavior files.

---

## How the Game Works

The simulation runs several MOOS *communities* — one per vehicle plus a
shoreside referee.  Each community has a database (MOOSDB) that processes
publish and subscribe to.

- **C++ track**: your code lives in **`pChallenge`**, which runs inside your
  vehicle's community and is started by `pAntler`.
- **Python track**: your script connects directly to the vehicle's MOOSDB as
  an external process.  Set `student_mode = "python"` in the scenario TOML
  and `pChallenge` is omitted from the generated `.moos` file.

```
Your vehicle community
  ┌──────────────────────────────────┐
  │  uSimMarine   (physics sim)      │
  │  pHelmIvP     (behavior engine)  │
  │  pNodeReporter                   │
  │  pChallenge   ← YOU CODE HERE    │
  └──────────────────────────────────┘
          ↕ NODE_REPORT (via pShare)
  Shoreside community
  ┌──────────────────────────────────┐
  │  pChallenge_shoreside (referee)  │
  │  pMarineViewer (GUI)             │
  └──────────────────────────────────┘
```

Your `pChallenge` process reads where you are and where other vehicles are,
then publishes MOOS variables that the IvP Helm behavior file (`walrus.bhv`)
reads to decide what to do.

---

## The MOOS Variable Interface

### Variables Your Code Reads (Subscribes To)

| Variable | Type | Meaning |
|----------|------|---------|
| `NAV_X` | double | Your vehicle's X position (metres from origin) |
| `NAV_Y` | double | Your vehicle's Y position (metres from origin) |
| `NAV_DEPTH` | double | Your vehicle's depth (metres, positive downward) |
| `NODE_REPORT` | string | Position + metadata for every other vehicle in the game |

#### Decoding a NODE_REPORT

```
NAME=walrus,TYPE=AUV,GROUP=alpha,X=-45.2,Y=-132.7,DEP=12.0,HDG=270.0,SPD=1.5,...
```

The `libBWSI` library parses this for you:

```cpp
// In Challenge.cpp — the tracker does this automatically
for (const NodeReport& contact : _tracker.contacts()) {
    double dist  = contact.distanceTo2D(_navX, _navY);  // 2-D range (m)
    double range = contact.rangeTo3D(_navX, _navY, _navDepth); // 3-D range (m)
    std::string who   = contact.name();   // e.g. "moby"
    std::string role  = contact.type();   // e.g. "AUV", "USV"
    std::string team  = contact.group();  // e.g. "alpha", "npc"
    double depth      = contact.depth();  // metres
}
```

### Variables Your Code Writes (Publishes)

These are read by the IvP Helm `.bhv` file to select and configure behaviors.

| Variable | Example value | Effect |
|----------|--------------|--------|
| `CLOSE` | `"true"` | Activates the `BHV_CutRange` chase behavior |
| `LOITER` | `"true"` | Activates the `BHV_Loiter` patrol behavior |
| `CHASE_UPDATES` | `"contact=moby"` | Tells the chase behavior which vehicle to pursue |

```cpp
// Chase a contact
Notify("CHASE_UPDATES", "contact=" + contact.name());
Notify("CLOSE",  "true");
Notify("LOITER", "false");

// Give up and patrol
Notify("CLOSE",  "false");
Notify("LOITER", "true");
```

---

## The ContactTracker Helper

`_tracker` (a `ContactTracker` from `libBWSI`) maintains a list of all
vehicles you have heard from.  It handles de-duplication automatically — each
vehicle appears exactly once, updated with its most recent position.

```cpp
// Iterate over all known contacts
for (const NodeReport& c : _tracker.contacts()) {
    if (c.group() == "npc") continue;         // skip NPC fish, sharks, etc.
    if (_tracker.isCollected(c)) continue;    // skip already-caught contacts

    double d = c.distanceTo2D(_navX, _navY);
    if (d < _maxChaseDist && !_tracker.isCollected(c)) {
        Notify("CHASE_UPDATES", "contact=" + c.name());
        Notify("CLOSE", "true");
        Notify("LOITER", "false");
        break; // pursue one target at a time
    }
}

// Mark a contact as handled
_tracker.markCollected(contact);
```

---

## Behavior File Primer (`.bhv`)

The IvP Helm reads the `.bhv` file to decide how to move the vehicle.
You do **not** edit the `.bhv` file directly in most challenges —
`pChallenge` drives it via MOOS variables.  But understanding how it
works helps you design better logic.

### Mode declarations

```
Set MODE = Active {
    DEPLOY = true
} Inactive

Set MODE = CHASING {
    MODE  = Active
    CLOSE = true
} LOITERING
```

This creates a state machine: when `CLOSE=true`, the helm enters `CHASING`
mode and runs the chase behavior; otherwise it loiters.

### Key behaviors you can drive

The generated `.bhv` file uses a three-way mode hierarchy for horizontal motion
plus `BHV_ConstantDepth` and `BHV_PeriodicSurface` for depth in serious missions.

| Variable to set | Mode entered | Behavior active |
|-----------------|--------------|-----------------|
| `CLOSE=true` | `Chasing` | `BHV_CutRange` — closes on named contact |
| `GO_TO=true` | `GoingTo` | `BHV_Waypoint` — follows waypoint list |
| neither | `Patrolling` | `BHV_Loiter` — circles patrol polygon |
| `DEPLOY=false` | `Inactive` | nothing |

Always-active safety behaviors:

| Behavior | Purpose |
|----------|---------|
| `BHV_OpRegion` | Hard arena boundary — stays inside polygon |
| `BHV_AvoidCollision` | Soft collision avoidance |
| `BHV_ConstantDepth` | *(GPS-denied only)* Holds search depth |
| `BHV_PeriodicSurface` | *(GPS-denied only)* Forces surface for GPS fix |

To dynamically update a behavior parameter at runtime, publish to its
`updates` variable:

```cpp
// Move the loiter center to a new position
Notify("LOITER_UPDATES", "center_assign=x=-50,y=-200");

// Change waypoint list mid-mission
Notify("WPT_UPDATE", "points=-50,-100:-80,-150:-20,-180,speed=1.5");

// Override depth (GPS-denied only)
Notify("DEPTH_UPDATES", "depth=20.0");
```

---

## Configuration Parameters

Add these to the `pChallenge` block in your `.moos` file:

```
ProcessConfig = pChallenge
{
    AppTick   = 4
    CommsTick = 4

    min_chase_dist = 5.0    // metres — contact counts as "caught" when inside this
    max_chase_dist = 50.0   // metres — start chasing when inside this
}
```

---

## Worked Example: Priority-Based Target Selection

The default implementation chases the nearest uncaught contact.  Here is a
slightly smarter version that prioritises treasures over whales over fish:

```cpp
bool Challenge::Iterate() {
    const NodeReport* bestTarget = nullptr;
    int bestPriority = -1;

    for (const NodeReport& c : _tracker.contacts()) {
        if (c.group() == "npc")           continue;
        if (_tracker.isCollected(c))      continue;

        int priority = 0;
        if (c.type() == "treasure") priority = 3;
        else if (c.type() == "whale")    priority = 2;
        else if (c.type() == "fish")     priority = 1;

        double d = c.distanceTo2D(_navX, _navY);
        if (d < _maxChaseDist && priority > bestPriority) {
            bestPriority = priority;
            bestTarget = &c;
        }
    }

    if (bestTarget) {
        double d = bestTarget->distanceTo2D(_navX, _navY);
        if (d < _minChaseDist) {
            _tracker.markCollected(*bestTarget);
            Notify("CLOSE",  "false");
            Notify("LOITER", "true");
        } else {
            Notify("CHASE_UPDATES", "contact=" + bestTarget->name());
            Notify("CLOSE",  "true");
            Notify("LOITER", "false");
        }
    } else {
        Notify("CLOSE",  "false");
        Notify("LOITER", "true");
    }
    return true;
}
```

---

---

## Decision-Making Under Uncertainty

Ocean autonomy involves noisy sensors, stale contacts, and vehicles that
cannot stop or turn instantly.  The full guide is in
**[DECISION_MAKING.md](DECISION_MAKING.md)**; the most useful patterns
are summarised here.

### Sensor confidence field

`pInfrastructureSensor` now includes a `confidence` field in every
detection message — the P_D value (0–1) used by the sensor model:

```
pipeline=cable_01,x=-101.2,y=-179.5,depth=30.0,
type=anomaly,anomaly_type=damage,range=12.4,confidence=0.587
```

Use this to weight your Bayesian updates: a detection at 5 m (confidence
≈ 0.83) is stronger evidence than one at 28 m (confidence ≈ 0.07).

### Bayesian log-odds belief tracking

Track whether a feature is present using a log-odds score:

**C++**
```cpp
#include "BeliefState.h"

BeliefState belief;

// For each detection message:
belief.updatePositive(detect.confidence, 0.02);  // PD, PFA

// Each iteration the sensor could observe but didn't:
belief.updateNegative(0.7, 0.02);

// Decay gradually when sensor moves away
belief.decay(0.98);

if (belief.decision(0.85))
    Notify("ANOMALY_REPORT_WALRUS", buildReport());
```

**Python**
```python
from api import DetectionBuffer

buf = DetectionBuffer(pd=0.7, pfa=0.02, decay=0.99)

if new_detection:
    buf.update_positive(pd=detect.confidence)  # use per-detection PD
else:
    buf.update_negative()
buf.tick_decay()

if buf.decision(threshold=0.85):
    api.notify("ANOMALY_REPORT_JELLYFISH", report_string)
    buf.reset()
```

### Contact staleness

Contacts are only as fresh as the last NODE_REPORT.  Use the C++
`ContactTracker` uncertainty helpers to avoid chasing ghosts:

```cpp
double age  = _tracker.contactAge("moby");          // seconds
double conf = _tracker.contactConfidence("moby", 8.0); // half-life 8 s

if (conf < 0.2)          // contact is stale — give up
    switchToLoiter();

// Dead-reckoning prediction
auto [px, py] = _tracker.predictPosition("moby", age);
```

In Python, each `Contact` has a `last_seen` timestamp:

```python
import time, math
age  = time.time() - c.last_seen
px   = c.x + c.speed * math.sin(math.radians(c.heading)) * age
py   = c.y + c.speed * math.cos(math.radians(c.heading)) * age
```

### Hysteresis — prevent mode-chattering

Require a condition to hold for several consecutive ticks before switching:

```python
chase_ticks = 0
REQUIRED = 3

while api.running:
    if candidate_in_range:
        chase_ticks += 1
        if chase_ticks >= REQUIRED:
            api.chase(target.name)
    else:
        chase_ticks = 0
        api.loiter()
    api.sleep(0.25)
```

See **[DECISION_MAKING.md](DECISION_MAKING.md)** for platform dynamics
(turn radius, underactuated constraints), CPA geometry for collision
avoidance, chance-constrained planning, and POMDP references.

---

## Tips

- **Time-warp**: Run with `--warp 4` during development to iterate faster.
  All MOOS timing (`MOOSTime()`, behavior durations) scales correctly.
- **AppCast**: In pMarineViewer, click your vehicle then the `pChallenge`
  row in the appcast panel to see live state.  Add `m_msgs << "..."` lines
  if you implement `AppCastingMOOSApp`.
- **uXMS**: Run `uXMS walrus.moos` in a terminal to watch MOOS variables
  update in real time — invaluable for debugging.
- **Depth matters**: The shark chases in 3-D.  Staying shallow or diving
  deep can break line-of-sight if you add comms range limits later.
- **Group filter**: Always check `contact.group() == "npc"` before acting
  on a contact — you do not want to chase the sharks.
- **GPS-denied depth**: While `BHV_PeriodicSurface` is active (vehicle ascending
  or at surface), horizontal behaviors are suspended.  Your loop keeps running —
  just wait for `api.at_surface` to go False before resuming waypoint commands.
- **Inspection clustering**: `pInfrastructureSensor` posts noisy detections at
  4 Hz.  Accumulate ~5 hits within 15 m before reporting an anomaly to avoid
  false positives.

---

## Example Scripts

| Script | Mission type | What it demonstrates |
|--------|-------------|----------------------|
| `student/examples/chase_nearest.py` | Game | Priority-based NPC targeting; `api.chase()` / `api.loiter()` |
| `student/examples/pipeline_survey.py` | Inspection | Subscribing to `INFRASTRUCTURE_DETECT`; detection clustering; `ANOMALY_REPORT` |
| `student/examples/beacon_nav.py` | GPS-denied | Trilateration from beacon ranges; `GPSDeniedVehicle` subclass; surface-event detection |

---

## Python API Reference

> Requires pymoos (installed alongside MOOS-IvP).

### Setup

In your scenario TOML, set `student_mode = "python"` on the vehicle:

```toml
[[teams.vehicles]]
name         = "jellyfish"
student_mode = "python"   # omits pChallenge from generated .moos
start_x      = 0.0
start_y      = -175.0
```

Then run your script after launching the mission:

```bash
./launch_game.sh --scenario scavenger_hunt
# in another terminal:
python student/examples/chase_nearest.py --vehicle jellyfish --port 9000
```

### VehicleAPI

```python
from api import VehicleAPI

api = VehicleAPI(
    vehicle_name = "jellyfish",
    server_port  = 9000,         # from scenario port assignment
    server_host  = "localhost",
    start_x      = 0.0,          # used by api.return_to_base()
    start_y      = -175.0,
)
api.start()          # blocks until MOOSDB connection established
```

### Own state

```python
api.x          # float — own X position (m)
api.y          # float — own Y position (m)
api.depth      # float — own depth (m, positive downward)
api.heading    # float — own heading (deg, 0=north, clockwise)
api.speed      # float — own speed (m/s)
api.deployed   # bool  — True when DEPLOY=true (mission active)
api.running    # bool  — True while connected AND deployed
api.position   # (x, y) tuple
```

### Contacts

```python
contacts = api.contacts()              # all known contacts
players  = [c for c in contacts if c.group != "npc"]
npcs     = [c for c in contacts if c.group == "npc"]
sharks   = [c for c in contacts if c.type.lower() == "shark"]

c = api.get_contact("moby")           # Contact or None

# Contact fields
c.name     # str   — e.g. "moby"
c.type     # str   — e.g. "AUV", "whale", "fish", "treasure"
c.group    # str   — e.g. "alpha", "npc"
c.x        # float
c.y        # float
c.depth    # float
c.heading  # float
c.speed    # float

c.distance_2d(api.x, api.y)          # horizontal range (m)
c.range_3d(api.x, api.y, api.depth)  # slant range (m)

# Collected-contact bookkeeping (local only — not visible to referee)
api.mark_collected(c)
api.is_collected(c)                    # bool
api.uncollected_contacts()             # list filtered by mark_collected
```

### Motion commands

```python
api.chase("moby")                      # close range on named contact
api.loiter()                           # resume default patrol polygon
api.loiter_at(-50, -200, radius=20)    # loiter around a specific point
api.go_to(-80, -130)                   # drive to a waypoint
api.go_to(-80, -130, speed=2.0)        # with custom speed
api.go_to_sequence([(-50,-100),(-80,-150),(-20,-180)])  # follow a route
api.go_to_sequence(..., repeat=True)   # cycle indefinitely
api.return_to_base()                   # go_to(start_x, start_y)
api.set_base(-60, -200)                # change return point
api.halt()                             # cancel all active commands
```

### Low-level access

```python
api.notify("MY_VAR", "some_string")   # publish a string variable
api.notify("MY_VAR", 3.14)            # publish a double variable
api.sleep(0.25)                        # time.sleep() wrapper
api.stop()                             # disconnect from MOOS
```

### Minimal mission template

```python
from api import VehicleAPI

api = VehicleAPI("jellyfish", server_port=9000)
api.start()

while not api.deployed:          # wait for instructor to hit DEPLOY
    api.sleep(0.1)

while api.running:
    # --- write your logic here ---
    npcs = [c for c in api.contacts()
            if c.group == "npc"
            and c.type.lower() != "shark"
            and not api.is_collected(c)]

    if npcs:
        target = min(npcs, key=lambda c: c.distance_2d(api.x, api.y))
        dist   = target.distance_2d(api.x, api.y)
        if dist < 7.0:
            api.mark_collected(target)
            api.loiter()
        else:
            api.chase(target.name)
    else:
        api.loiter()

    api.sleep(0.25)

api.stop()
```

---

## Extending VehicleAPI for Serious Missions

`VehicleAPI` subscribes to the standard navigation variables on startup.
For serious missions you need additional subscriptions.  The cleanest way
is to subclass and override `_on_connect`:

```python
from api import VehicleAPI

class InspectionVehicle(VehicleAPI):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._detections = []    # INFRASTRUCTURE_DETECT messages

    def _on_connect(self):
        super()._on_connect()
        self._comms.register("INFRASTRUCTURE_DETECT", 0)
        return True

    def _on_new_mail(self, messages):
        super()._on_new_mail(messages)
        with self._lock:
            for msg in messages:
                if msg.key() == "INFRASTRUCTURE_DETECT":
                    self._detections.append(msg.string())
        return True
```

The GPS-denied example (`beacon_nav.py`) uses this pattern as `GPSDeniedVehicle`,
adding `BEACON_RANGE_REPORT` and `VEHICLE_AT_SURFACE` subscriptions.

### Inspection mission additions

```python
# After receiving INFRASTRUCTURE_DETECT messages and clustering them,
# report a confirmed anomaly:
api.notify("ANOMALY_REPORT_JELLYFISH",
           "pipeline=cable_01,x=-101.2,y=-179.5,"
           "type=anomaly,anomaly_type=damage,count=7")
```

`pInspectionScorer` on the shoreside receives this, matches it against
ground truth within 15 m, and awards points (or deducts for a false alarm).

### GPS-denied mission additions

```python
# Extra state properties available on GPSDeniedVehicle:
api.at_surface          # bool — True while BHV_PeriodicSurface has control
api.beacon_ranges       # dict — {"beacon_01": 42.3, ...}
api.acoustic_position   # (x, y) tuple — smoothed trilateration estimate

# Called in the loop to update the acoustic estimate:
pos = api.update_acoustic_position()

# Set depth (overrides BHV_ConstantDepth default):
api.notify("DEPTH_UPDATES", "depth=20.0")
```
