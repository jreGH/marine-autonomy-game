# Student Behavior Development Guide

This guide explains how to program your vehicle's autonomy for the BWSI
AUVC challenge.  You do not need to understand all of MOOS-IvP to
compete — this document covers everything your code needs to know.

---

## How the Game Works

The simulation runs several MOOS *communities* — one per vehicle plus a
shoreside referee.  Each community has a database (MOOSDB) that processes
publish and subscribe to.  Your code lives in **`pChallenge`**, which runs
inside your vehicle's community.

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

| Behavior | Condition variable | Updates variable | What it does |
|---|---|---|---|
| `BHV_CutRange` | `MODE==CHASING` | `CHASE_UPDATES` | Closes range to a named contact |
| `BHV_Loiter` | `MODE==LOITERING` | `LOITER_UPDATES` | Circles a polygon |
| `BHV_Waypoint` | user-defined | `WPT_UPDATE` | Follows a list of waypoints |
| `BHV_StationKeep` | user-defined | — | Holds a fixed point |
| `BHV_AvoidCollision` | always active | — | Safety — avoids contacts |
| `BHV_OpRegion` | always active | — | Safety — stays inside arena |

To dynamically update a behavior parameter at runtime, publish to its
`updates` variable:

```cpp
// Move the loiter center to a new position
Notify("LOITER_UPDATES", "center_assign=x=-50,y=-200");

// Change waypoint list mid-mission
Notify("WPT_UPDATE", "points=-50,-100:-80,-150:-20,-180");
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
