# BWSI Mission Builder — Instructor User Guide

The Mission Builder is a browser-based tool for designing BWSI AUVC scenarios
without writing TOML by hand.  You place geometry on a real map, configure the
sensor model and scoring, and download a ready-to-run scenario file.

---

## Quick Start

```bash
# Install dependencies (one-time)
pip install flask pillow

# Launch the builder
cd tools/mission_builder
python app.py

# Open in your browser
# http://localhost:5050
```

---

## Workflow Overview

```
1. Set origin & load map
       ↓
2. Draw mission geometry
       ↓
3. Place vehicles
       ↓
4. Configure sensor & scoring
       ↓
5. Validate & export TOML
       ↓
6. Generate & run with deploy.sh
```

---

## Step 1: Set Origin and Load the Background Map

The **origin** is the (0, 0) point of the MOOS local XY coordinate system —
every other position in the scenario is expressed as metres east (x) and
metres north (y) from this point.  Choose a location inside your intended
mission area.

1. Enter the origin **Lat** and **Lon** in the header fields.
2. Select a map source from the dropdown:
   - **OSM** — OpenStreetMap (default; no download needed)
   - **ESRI Satellite** — aerial/satellite imagery
   - **CartoDB Light** — clean, minimal basemap
   - **NOAA Chart** — US nautical raster charts (good for coastal areas)
3. Click **Load Map**.

For OSM, tiles are served directly from the browser with no server round-trip.
For all other sources, the server downloads and stitches tiles for a ~700 m
radius around the origin and serves them as a single image overlay.  This
creates a `background.png` file suitable for use as a pMarineViewer `tiff_file`
(see Step 5).

A yellow dot marks the origin (x=0, y=0) on the map.  Hovering anywhere on
the map shows the lat/lon and corresponding MOOS XY in the bottom-left tooltip.

---

## Step 2: Draw Mission Geometry

Select a draw mode from the **Draw** toolbar, then interact with the map:

### Arena (operation boundary)

Select **Arena** mode.  Click to place polygon corners; double-click to close
the polygon.  The arena polygon becomes the `[arena] vertices` in the TOML and
is enforced by `BHV_OpRegion` in all vehicle behavior files.

Only one arena polygon is used; drawing a second one replaces the first.

### Pipeline (inspection mission)

Select **Pipeline** mode.  Click to place waypoints along the cable/pipeline
route; double-click to finish the polyline.  Each polyline becomes one
`[[pipelines]]` entry.  You can draw multiple pipelines.

The pipeline depth defaults to 10 m.  To change it, edit the exported TOML
directly.

### Anomaly (inspection mission)

Select **Anomaly** mode.  Click to place an anomaly point.  A dialog asks:
- **Pipeline label** — which pipeline this anomaly belongs to (e.g. `cable_01`)
- **Type** — `damage`, `corrosion`, or `obstruction`

Anomalies become `[[anomalies]]` entries.

### Mine (MCM mission)

Select **Mine** mode.  Two click types place different mine types:
- **Left-click** → benign contact (rock, wreck)
- **Right-click** → live mine (hazard)

Each mine is auto-labeled `m01`, `m02`, … and becomes a `[[mines]]` entry.

The mine field is **ground truth** — it is passed to `uFldHazardSensor` but
never shown to students.

### Vehicle

Select **Vehicle** mode.  Click to place a vehicle start position.  A dialog
asks:
- **Vehicle name** — unique identifier (e.g. `jellyfish`)
- **Team name** — vehicles on the same team share a droplet in multi-host mode
- **Start heading** — initial compass bearing in degrees (0 = north)

---

## Step 3: Configure Mission Type, Sensor, and Scoring

Use the **right sidebar** to configure:

### Mission panel

| Field | Description |
|-------|-------------|
| Type | MCM, Inspection, Game, or GPS-Denied — controls which generator runs |
| Name | Human-readable label; becomes the downloaded filename |
| Description | Free-form text included in the TOML header comment |
| Map file | Filename passed to pMarineViewer's `tiff_file` parameter |

### Sensor panel (MCM)

| Field | Description |
|-------|-------------|
| sensor_pd | Probability of detection per sensor pass (0–1) |
| sensor_pfa | Probability of false alarm per pass |
| sensor_width | Swath half-width in metres — set equal to your lane width |
| sensor_exp | ROC curve exponent (higher = sharper roll-off) |
| classify_pd | Probability of correct classification |
| classify_time | Seconds required for one classification |

### Sensor panel (Inspection)

| Field | Description |
|-------|-------------|
| detect_range | Maximum detection range in metres |
| detect_cone | Half-angle of the forward detection cone in degrees |
| noise_sigma | Standard deviation of position noise on detections |
| p_false_alarm | False alarm probability per vehicle per second |

### Scoring panel (MCM)

| Field | Description |
|-------|-------------|
| penalty_missed | Points lost per unreported hazard |
| penalty_false_alarm | Points lost per benign reported as hazard |
| max_time | Mission time limit in seconds |

---

## Step 4: Validate

Click **Validate** in the Export section.  The builder checks:

- All required sections present (origin, arena, teams)
- Origin lat/lon in valid range
- Arena has at least 3 vertices
- Mission-type geometry present (at least one mine for MCM, one pipeline for Inspection)
- No duplicate vehicle names
- All vehicle start positions inside the arena bounding box

Errors are listed in red below the button.  Fix each one before exporting.

---

## Step 5: Export the TOML

Click **Download TOML**.  The browser downloads `<mission_name>.toml` to your
downloads folder.  Copy it to the appropriate scenarios directory:

```
missions/mcm/scenarios/my_minefield.toml
missions/inspection/scenarios/my_pipeline.toml
```

The exported TOML is identical in format to the hand-written examples under
`missions/*/scenarios/` and is immediately usable by the generator scripts.

---

## Step 6: Generate and Run the Mission

### Single-host (local development)

```bash
# MCM
python3 missions/mcm/gen_mcm.py \
    --scenario missions/mcm/scenarios/my_minefield.toml

cd missions/mcm/run/my_minefield
./launch_all_local.sh 4        # time warp 4×

# Inspection
python3 missions/inspection/gen_inspection.py \
    --scenario missions/inspection/scenarios/my_pipeline.toml
```

Or use the convenience wrapper:

```bash
missions/mcm/launch_mcm.sh --scenario missions/mcm/scenarios/my_minefield.toml --warp 4
```

### Multi-host (DigitalOcean / cloud)

Add a `[deployment]` section to the TOML before running (or add it in the
exported file):

```toml
[deployment]
shoreside_host = "165.22.100.50"

[deployment.vehicle_hosts]
alpha = "142.93.50.10"
bravo = "142.93.50.11"
```

Then deploy with the one-shot script:

```bash
./deploy.sh --scenario missions/mcm/scenarios/my_minefield.toml --warp 4
```

`deploy.sh` generates the mission files, SCPs them to the appropriate droplets,
and starts Docker Compose on each host.  The web dashboard is available at
`http://<shoreside_host>:8080`.

---

## Understanding Coordinate Conversion

All positions in the TOML are **MOOS local XY metres**:
- `x` = metres east of origin (positive = east)
- `y` = metres north of origin (positive = north)

The builder converts lat/lon to XY automatically when you click the map.  You
can also use the Python utilities directly:

```python
from tools.mission_builder.map_utils import latlon_to_xy, xy_to_latlon

x, y = latlon_to_xy(43.826, -70.328, origin_lat=43.8253, origin_lon=-70.3304)
# x ≈ 177 m east, y ≈ 80 m north

lat, lon = xy_to_latlon(177, 80, origin_lat=43.8253, origin_lon=-70.3304)
```

The formula is the same flat-earth equirectangular projection used internally
by MOOS-IvP — accurate to < 1 % for distances up to ~100 km from the origin.

---

## MCM Mission: How It Works End-to-End

```
Vehicle Python script
  ↓ posts UHZ_SENSOR_REQUEST = vname=jellyfish   (request a sensor sweep)
  ↑ receives UHZ_DETECTION_REPORT                (list of detected contacts)
  ↓ posts UHZ_CLASSIFY_REQUEST = vname=...,label=m01  (request classification)
  ↑ receives UHZ_CLASSIFY_REPORT                 (hazard or benign?)
  ↓ posts UHZ_HAZARD_REPORT = vname=...,label=m01,type=hazard,x=...,y=...
                                                  (report to shoreside for scoring)
```

`uFldHazardSensor` (runs on the shoreside Tier 1 server) handles requests and
applies the sensor model.  `uFldHazardMetric` scores final reports against
ground truth at the end of the mission.

The lawnmower survey pattern is pre-computed by `gen_mcm.py` from the arena
vertices and `lane_width` parameter (set equal to `sensor_width` so every point
in the arena falls within at least one swath).  Multiple vehicles are
automatically staggered by half a lane width so they cover different strips.

Student code controls **when** to send sensor requests (typically on a timer or
after each waypoint) and **what decision logic** to apply to the reports.

---

## Using `toml_writer` and `map_utils` Programmatically

If you want to generate scenarios from a script rather than the web UI:

```python
from tools.mission_builder.toml_writer import write_toml, validate
from tools.mission_builder.map_utils import latlon_to_xy

# Build a scenario dict
origin_lat, origin_lon = 43.8253, -70.3304

mines = []
for i, (lat, lon, kind) in enumerate([
    (43.824, -70.332, "hazard"),
    (43.825, -70.328, "benign"),
]):
    x, y = latlon_to_xy(lat, lon, origin_lat, origin_lon)
    mines.append({"label": f"m{i+1:02d}", "x": round(x,1), "y": round(y,1), "type": kind})

scenario = {
    "scenario": {"name": "Scripted MCM", "type": "mcm"},
    "origin":   {"lat": origin_lat, "lon": origin_lon},
    "arena":    {"vertices": [[-200,-300],[200,-300],[200,0],[-200,0]]},
    "mines":    mines,
    "sensor":   {"sensor_pd": 0.85, "sensor_pfa": 0.04, "sensor_width": 25,
                 "sensor_exp": 6, "classify_pd": 0.75, "classify_time": 10},
    "scoring":  {"penalty_missed_hazard": 150, "penalty_false_alarm": 75, "max_time": 900},
    "survey":   {"lane_width": 25, "survey_speed": 2.5},
    "teams": [
        {"name": "alpha", "color": "dodger_blue", "vehicles": [
            {"name": "jellyfish", "student_mode": "python",
             "start_x": -150, "start_y": -20, "start_heading": 180, "max_speed": 4.0}
        ]}
    ],
}

errors = validate(scenario)
if errors:
    print("Validation errors:", errors)
else:
    toml_text = write_toml(scenario)
    with open("missions/mcm/scenarios/scripted.toml", "w") as f:
        f.write(toml_text)
```

---

## File Reference

```
tools/mission_builder/
├── app.py              Flask web server — run this
├── map_utils.py        Coordinate conversion + tile download
├── toml_writer.py      TOML serialiser + scenario validator
├── requirements.txt    pip install -r requirements.txt
└── templates/
    └── builder.html    Single-page map editor

missions/mcm/
├── gen_mcm.py          Mission generator (reads TOML, writes .moos/.bhv)
├── launch_mcm.sh       Convenience wrapper for local runs
├── scenarios/
│   └── mcm_example.toml   Reference scenario (5 mines, 2 teams)
└── templates/
    ├── shoreside.moos.template
    ├── vehicle.moos.template
    └── vehicle.bhv.template
```
