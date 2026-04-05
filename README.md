# BWSI AUVC — Autonomous Underwater Vehicle Competition

Beaver Works Summer Institute course materials and game framework for a
team-based autonomous underwater vehicle competition built on
[MOOS-IvP](https://oceanai.mit.edu/moos-ivp/pmwiki/pmwiki.php).

---

## What Is This?

Students program the autonomy of simulated underwater vehicles (AUVs) to
compete in a multi-team ocean scavenger hunt.  The game engine is MOOS-IvP —
the same open-source middleware and behavior-based autonomy architecture used
on real research AUVs at MIT, WHOI, and the US Navy.

There are two tracks:

| Track | Description |
|-------|-------------|
| **Game mode** | Contrived scavenger-hunt scenarios designed to teach autonomy concepts quickly.  Teams chase whales, photograph fish, collect treasure, and evade NPC sharks. |
| **Serious mode** | Realistic maritime missions: GPS-denied area search, mine countermeasures, and undersea infrastructure inspection. |

---

## Prerequisites

1. **MOOS-IvP** built and installed at `~/moos-ivp/`.
   Follow the official install guide at
   <https://oceanai.mit.edu/moos-ivp/pmwiki/pmwiki.php?n=PMwikiUsers.InstallingMOOS-IvP>

2. **C++ toolchain** — `g++` with C++11 support (`sudo apt install build-essential` on Ubuntu).

3. *(Optional, for serious missions)* **Python 3** with `pymoos` for the vehicle API:
   ```bash
   pip install pymoos
   ```

---

## Repository Layout

```
bwsiauvc-summer-2022/
├── README.md                    ← you are here
├── code_to_students/
│   └── moos-bwsi/
│       ├── build_all.sh         ← build the whole game
│       ├── lib/
│       │   └── libBWSI/         ← shared C++ library (NodeReport, ContactTracker)
│       ├── behaviors/
│       │   ├── pChallenge/      ← STUDENT vehicle logic (edit this)
│       │   ├── pChallenge_shark/
│       │   ├── pChallenge_fish/
│       │   ├── pChallenge_whale/
│       │   ├── pChallenge_treasure/
│       │   ├── pChallenge_shoreside/
│       │   └── cpp_test/        ← C++ tutorial exercises
│       └── missions/
│           └── challenge_01/    ← mission launch files and .bhv configs
├── code_to_instructors/         ← instructor reference implementations
└── cpp_intro/                   ← standalone C++ warm-up exercises
```

---

## Building

```bash
# 1. Clone the repo so it lives at ~/moos-bwsi
git clone <repo-url> ~/moos-bwsi

# 2. Build everything (library first, then all apps)
cd ~/moos-bwsi
./build_all.sh
```

Binaries are installed to `~/moos-bwsi/behaviors/bin/`.  Make sure that
directory is on your `PATH`:

```bash
echo 'export PATH=$PATH:$HOME/moos-bwsi/behaviors/bin' >> ~/.bashrc
source ~/.bashrc
```

---

## Running the Challenge

```bash
cd ~/moos-bwsi/missions/challenge_01
./launch.sh --warp 4          # run at 4× real-time for faster testing
```

The pMarineViewer GUI will open.  Press **DEPLOY** to start the vehicles.
The appcast panel (bottom-right) shows live status for every process,
including the current score from `pChallenge_shoreside`.

To run without a GUI (e.g. on a headless server):

```bash
./launch.sh --warp 10 --nogui
```

---

## Where Students Work

Open `behaviors/pChallenge/Challenge.cpp`.  That is the student's vehicle
logic.  The `Iterate()` method is called at 4 Hz; use the `_tracker` contact
list and call `Notify()` to command the IvP Helm.

See **[STUDENT_GUIDE.md](code_to_students/moos-bwsi/STUDENT_GUIDE.md)** for
the full interface reference, behavior composition guide, and worked examples.

---

## Serious Missions

GPS-denied area search, mine countermeasures, and undersea infrastructure
inspection are documented in
**[SERIOUS_MISSIONS.md](code_to_students/moos-bwsi/SERIOUS_MISSIONS.md)**.
