# BWSI AUVC — Autonomous Underwater Vehicle Competition

Beaver Works Summer Institute course materials and game framework for a
team-based autonomous underwater vehicle competition built on
[MOOS-IvP](https://oceanai.mit.edu/moos-ivp/pmwiki/pmwiki.php).

---

## What Is This?

Students program the autonomy of simulated underwater vehicles (AUVs) to
compete in multi-team ocean missions.  The simulation engine is MOOS-IvP —
the same open-source middleware and behavior-based autonomy architecture used
on real research AUVs at MIT, WHOI, and the US Navy.

Two tracks are supported:

| Track | Description |
|-------|-------------|
| **Game mode** | Contrived scavenger-hunt scenario designed to teach autonomy concepts quickly.  Teams chase whales, photograph fish, collect treasure, and evade NPC sharks. |
| **Serious mode** | Realistic maritime missions: GPS-denied acoustic navigation and undersea infrastructure inspection. |

Students may write their vehicle logic in **C++** (editing `pChallenge`) or
**Python** (using `student/api/VehicleAPI.py`).  Both tracks publish the same
MOOS variables and compose with the same `.bhv` behavior files.

---

## Prerequisites

1. **MOOS-IvP** built and installed at `~/moos-ivp/`.
   Follow the official install guide at
   <https://oceanai.mit.edu/moos-ivp/pmwiki/pmwiki.php?n=PMwikiUsers.InstallingMOOS-IvP>

2. **C++ toolchain** — `g++` with C++11 support:
   ```bash
   sudo apt install build-essential
   ```

3. **Python 3.11+** (or Python 3.8+ with `pip install tomli`).

4. *(Python track)* **pymoos** — Python bindings for MOOS, bundled with MOOS-IvP:
   ```bash
   pip install pymoos
   ```

5. *(Optional)* **matplotlib** for pre-mission briefing graphics:
   ```bash
   pip install matplotlib
   ```

---

## Repository Layout

```
bwsiauvc-summer-2022/
├── README.md                          ← you are here
├── code_to_students/
│   └── moos-bwsi/
│       ├── build_all.sh               ← build all C++ apps
│       ├── STUDENT_GUIDE.md           ← programming interface reference
│       ├── SERIOUS_MISSIONS.md        ← serious mission design docs
│       │
│       ├── lib/
│       │   └── libBWSI/               ← shared C++ library
│       │       ├── NodeReport.h/.cpp  ← NODE_REPORT parser
│       │       └── ContactTracker.h/.cpp
│       │
│       ├── behaviors/
│       │   ├── pChallenge/            ← STUDENT vehicle logic (edit this)
│       │   ├── pChallenge_shark/      ← NPC: shark pursuer
│       │   ├── pChallenge_fish/       ← NPC: fish evader
│       │   ├── pChallenge_whale/      ← NPC: whale
│       │   ├── pChallenge_treasure/   ← NPC: treasure
│       │   ├── pChallenge_shoreside/  ← game referee / scoreboard
│       │   ├── pInfrastructureSensor/ ← inspection: sonar sensor oracle
│       │   └── pInspectionScorer/     ← inspection: coverage + anomaly scorer
│       │
│       ├── missions/
│       │   ├── game/                  ← scavenger hunt (game mode)
│       │   │   ├── scenarios/         ← TOML scenario configs
│       │   │   ├── templates/         ← .moos / .bhv templates
│       │   │   ├── gen_mission.py     ← mission file generator
│       │   │   └── launch_game.sh     ← top-level launcher
│       │   ├── inspection/            ← pipeline survey (serious mode)
│       │   │   ├── scenarios/
│       │   │   ├── templates/
│       │   │   ├── gen_inspection.py
│       │   │   └── launch_inspection.sh
│       │   └── gps_denied/            ← acoustic navigation (serious mode)
│       │       ├── scenarios/
│       │       ├── templates/
│       │       ├── gen_gps_denied.py
│       │       └── launch_gps_denied.sh
│       │
│       ├── student/
│       │   ├── api/
│       │   │   └── VehicleAPI.py      ← Python vehicle interface
│       │   └── examples/
│       │       ├── chase_nearest.py   ← game mode starter
│       │       ├── pipeline_survey.py ← inspection starter
│       │       └── beacon_nav.py      ← GPS-denied starter
│       │
│       └── briefing/
│           ├── gen_briefing.py        ← pre-mission brief (PNG + text)
│           └── post_visuals.py        ← inject visuals into live pMarineViewer
│
├── code_to_instructors/               ← instructor reference implementations
└── cpp_intro/                         ← standalone C++ warm-up exercises
```

---

## Building

```bash
# From inside the moos-bwsi directory:
cd code_to_students/moos-bwsi
./build_all.sh
```

This builds `libBWSI` first, then all seven C++ apps in dependency order.
Binaries are installed to `~/moos-bwsi/behaviors/bin/`.  Add that to your PATH:

```bash
echo 'export PATH=$PATH:$HOME/moos-bwsi/behaviors/bin' >> ~/.bashrc
source ~/.bashrc
```

---

## Running Missions

All three mission types share the same workflow: pick a scenario, run the
launcher, and the tool generates MOOS config files, prints a text briefing,
and optionally saves a PNG briefing image before starting MOOS.

### Game mode — Scavenger Hunt

```bash
cd code_to_students/moos-bwsi/missions/game
./launch_game.sh --scenario scavenger_hunt --warp 4
```

The pMarineViewer GUI opens.  Press **DEPLOY** to start the vehicles.
The appcast panel shows live scores from `pChallenge_shoreside`.

### Serious mode — Pipeline Inspection

```bash
cd code_to_students/moos-bwsi/missions/inspection
./launch_inspection.sh --scenario pipeline_survey --warp 4
```

Vehicles detect the cable corridor via `pInfrastructureSensor`; `pInspectionScorer`
tracks coverage and grades anomaly reports in real time.

### Serious mode — GPS-Denied Navigation

```bash
cd code_to_students/moos-bwsi/missions/gps_denied
./launch_gps_denied.sh --scenario beacon_nav --warp 4
```

Vehicles dive to 15 m and navigate by acoustic beacon ranging.
`BHV_PeriodicSurface` brings them up every 60 s for a GPS fix.

### Common launcher flags

| Flag | Effect |
|------|--------|
| `--warp N` | Run at N× real-time (e.g. `--warp 4` for fast iteration) |
| `--clean` | Delete the previous run directory before regenerating |
| `--help` | Show available scenarios and options |

---

## Where Students Work

### C++ track

Edit `behaviors/pChallenge/Challenge.cpp`.  The `Iterate()` method is called
at 4 Hz; read contacts from `_tracker` and call `Notify()` to drive the helm.

### Python track

Set `student_mode = "python"` on a vehicle in the scenario TOML, then run your
script after launching:

```bash
python student/examples/chase_nearest.py --vehicle jellyfish --port 9000
```

The `VehicleAPI` class handles the MOOS connection, contact parsing, and motion
commands.  No MOOS or C++ knowledge required.

See **[STUDENT_GUIDE.md](code_to_students/moos-bwsi/STUDENT_GUIDE.md)** for
the full interface reference, behavior composition guide, and worked examples
for all three mission types.

---

## Pre-Mission Briefings

The launcher scripts automatically generate a mission brief before starting
MOOS.  To generate a brief manually:

```bash
# Text summary (always available)
python briefing/gen_briefing.py --scenario missions/game/scenarios/scavenger_hunt.toml

# PNG figure (requires matplotlib)
python briefing/gen_briefing.py \
  --scenario missions/inspection/scenarios/pipeline_survey.toml \
  --output /tmp/brief.png
```

To inject static visual features (arena boundary, pipelines, beacons) into
the live pMarineViewer after the shoreside starts:

```bash
python briefing/post_visuals.py \
  --scenario missions/inspection/scenarios/pipeline_survey.toml
```

---

## Serious Missions

Design rationale, MOOS-IvP application references, MOOS variable tables, and
scoring details for all serious missions are in
**[SERIOUS_MISSIONS.md](code_to_students/moos-bwsi/SERIOUS_MISSIONS.md)**.
