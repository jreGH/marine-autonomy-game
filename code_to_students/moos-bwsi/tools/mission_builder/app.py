"""
app.py — BWSI AUVC Mission Builder web application
===================================================

An interactive tool for instructors to design missions by:
  1. Entering an origin lat/lon and downloading a background map tile
  2. Drawing mission geometry (pipelines, mines, beacons, arena polygon)
     on a Leaflet.js map — all lat/lon clicks auto-convert to local MOOS XY
  3. Configuring sensor model, scoring, and teams in a side panel
  4. Exporting the completed scenario as a ready-to-run TOML file

Usage:
    pip install flask pillow
    python app.py [--port 5050]

Then open http://localhost:5050 in your browser.

The app is single-user / local only — no authentication.
"""

import json
import math
import os
import sys
import argparse
import tempfile
import textwrap
from pathlib import Path

from flask import Flask, jsonify, render_template, request, send_file

# Add tools/ directory to import path so we can use map_utils / toml_writer
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from map_utils import latlon_to_xy, xy_to_latlon, bbox_from_origin_and_radius, download_tiles, BBox
from toml_writer import write_toml, validate

# ---------------------------------------------------------------------------
# Flask app
# ---------------------------------------------------------------------------

app = Flask(__name__)

# Temporary directory for downloaded map tiles (cleared on restart)
_TILE_DIR = Path(tempfile.mkdtemp(prefix="bwsi_builder_"))

# In-memory scenario state — keyed by session (single-user: just "default")
_scenario: dict = {}


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    return render_template("builder.html")


@app.route("/api/convert_latlon", methods=["POST"])
def api_convert_latlon():
    """
    Convert a lat/lon click to local MOOS XY given the current origin.

    Body: {"lat": float, "lon": float, "origin_lat": float, "origin_lon": float}
    Returns: {"x": float, "y": float}
    """
    d = request.get_json(force=True)
    try:
        x, y = latlon_to_xy(
            float(d["lat"]), float(d["lon"]),
            float(d["origin_lat"]), float(d["origin_lon"]),
        )
        return jsonify({"ok": True, "x": round(x, 2), "y": round(y, 2)})
    except (KeyError, ValueError) as e:
        return jsonify({"ok": False, "error": str(e)}), 400


@app.route("/api/convert_xy", methods=["POST"])
def api_convert_xy():
    """
    Convert local MOOS XY back to lat/lon.

    Body: {"x": float, "y": float, "origin_lat": float, "origin_lon": float}
    Returns: {"lat": float, "lon": float}
    """
    d = request.get_json(force=True)
    try:
        lat, lon = xy_to_latlon(
            float(d["x"]), float(d["y"]),
            float(d["origin_lat"]), float(d["origin_lon"]),
        )
        return jsonify({"ok": True, "lat": round(lat, 7), "lon": round(lon, 7)})
    except (KeyError, ValueError) as e:
        return jsonify({"ok": False, "error": str(e)}), 400


@app.route("/api/download_map", methods=["POST"])
def api_download_map():
    """
    Download and stitch background map tiles for the given origin + radius.

    Body:
        {
            "origin_lat":  float,
            "origin_lon":  float,
            "radius_m":    float,   # half-width of area to cover (default 600)
            "zoom":        int,     # tile zoom level (default 16)
            "tile_source": str,     # "osm" | "esri_satellite" | ... (default "osm")
        }

    Returns:
        {"ok": true, "tile_url": "/tiles/<filename>", "origin_lat": ..., "origin_lon": ...}
    """
    d = request.get_json(force=True)
    try:
        origin_lat  = float(d["origin_lat"])
        origin_lon  = float(d["origin_lon"])
        radius_m    = float(d.get("radius_m",    600))
        zoom        = int(d.get("zoom",           16))
        tile_source = str(d.get("tile_source",   "osm"))
    except (KeyError, ValueError) as e:
        return jsonify({"ok": False, "error": str(e)}), 400

    bbox = bbox_from_origin_and_radius(origin_lat, origin_lon, radius_m)
    png_path = _TILE_DIR / "background.png"

    try:
        result = download_tiles(bbox, zoom, str(png_path), tile_source=tile_source)
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

    return jsonify({
        "ok":         True,
        "tile_url":   "/tiles/background.png",
        "tfw_url":    "/tiles/background.png.tfw",
        "origin_lat": result["origin_lat"],
        "origin_lon": result["origin_lon"],
        "pixel_size_m": result["pixel_size_m"],
        "tile_count": result["tile_count"],
    })


@app.route("/tiles/<filename>")
def serve_tile(filename: str):
    """Serve downloaded tile PNG and world file."""
    path = _TILE_DIR / filename
    if not path.exists():
        return "Not found", 404
    return send_file(str(path))


@app.route("/api/validate", methods=["POST"])
def api_validate():
    """
    Validate the current scenario dict.

    Body: the scenario dict (JSON)
    Returns: {"ok": bool, "errors": [...]}
    """
    d = request.get_json(force=True)
    errors = validate(d)
    return jsonify({"ok": len(errors) == 0, "errors": errors})


@app.route("/api/export_toml", methods=["POST"])
def api_export_toml():
    """
    Validate and export a scenario dict as a TOML file download.

    Body: the scenario dict (JSON)
    Returns: TOML file download (Content-Disposition: attachment)
    """
    d = request.get_json(force=True)
    errors = validate(d)
    if errors:
        return jsonify({"ok": False, "errors": errors}), 400

    toml_text = write_toml(d)
    mission_name = d.get("scenario", {}).get("name", "scenario")
    filename = mission_name.lower().replace(" ", "_") + ".toml"

    # Write to a temp file and send
    tmp = tempfile.NamedTemporaryFile(
        mode="w", suffix=".toml", delete=False, prefix="bwsi_"
    )
    tmp.write(toml_text)
    tmp.close()

    return send_file(
        tmp.name,
        as_attachment=True,
        download_name=filename,
        mimetype="text/plain",
    )


@app.route("/api/save_state", methods=["POST"])
def api_save_state():
    """
    Persist the current in-memory scenario state (for page reload recovery).
    Body: scenario dict (JSON)
    """
    global _scenario
    _scenario = request.get_json(force=True)
    return jsonify({"ok": True})


@app.route("/api/load_state")
def api_load_state():
    """Return the last saved scenario state (empty dict if none)."""
    return jsonify(_scenario)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="BWSI AUVC Mission Builder")
    parser.add_argument("--port", type=int, default=5050,
                        help="HTTP port (default: 5050)")
    parser.add_argument("--host", default="127.0.0.1",
                        help="Listen address (default: 127.0.0.1 — local only)")
    args = parser.parse_args()

    print(f"Mission Builder: http://{args.host}:{args.port}")
    print(f"  Tile cache:    {_TILE_DIR}")
    print()
    app.run(host=args.host, port=args.port, debug=False)


if __name__ == "__main__":
    main()
