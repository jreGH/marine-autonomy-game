"""
app.py — BWSI AUVC web status dashboard
========================================

Connects to the shoreside MOOSDB via pymoos, subscribes to mission-critical
variables, and exposes them over a small Flask API.  The browser polls
/api/state every second and renders vehicle positions on a Leaflet.js map.

Environment variables:
  SHORESIDE_HOST  IP of the shoreside MOOSDB (default: localhost)
  SHORESIDE_PORT  Port of the shoreside MOOSDB (default: 9100)
  WEB_PORT        HTTP port for this server (default: 8080)
"""

import json
import math
import os
import threading
import time
from collections import defaultdict

from flask import Flask, jsonify, render_template

try:
    import pymoos
    MOOS_AVAILABLE = True
except ImportError:
    MOOS_AVAILABLE = False

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

SHORE_HOST = os.environ.get("SHORESIDE_HOST", "localhost")
SHORE_PORT = int(os.environ.get("SHORESIDE_PORT", 9100))
WEB_PORT   = int(os.environ.get("WEB_PORT", 8080))

# ---------------------------------------------------------------------------
# Shared state (updated by MOOS thread, read by Flask thread)
# ---------------------------------------------------------------------------

_lock     = threading.Lock()
_vehicles = {}   # name → {x, y, depth, heading, speed, type, group, time}
_score    = ""   # last INSPECTION_SCORE or GAME_SCORE value
_deploy   = False
_running  = True

# ---------------------------------------------------------------------------
# MOOS subscriber
# ---------------------------------------------------------------------------

def parse_node_report(raw: str) -> dict:
    """Parse KEY=VALUE,... NODE_REPORT string into a dict."""
    d = {}
    for token in raw.split(","):
        if "=" in token:
            k, _, v = token.partition("=")
            d[k.strip().upper()] = v.strip()
    return d


class ShoresideSubscriber:
    """Connects to shoreside MOOSDB and updates the shared state dicts."""

    def __init__(self):
        self._comms = pymoos.comms()
        self._comms.set_on_connect_callback(self._on_connect)
        self._comms.set_on_new_mail_callback(self._on_mail)
        self._comms.run(SHORE_HOST, SHORE_PORT, "bwsi_web_ui")

    def _on_connect(self):
        self._comms.register("NODE_REPORT", 0)
        self._comms.register("INSPECTION_SCORE", 0)
        self._comms.register("GAME_SCORE", 0)
        self._comms.register("DEPLOY_ALL", 0)
        return True

    def _on_mail(self):
        global _deploy, _score
        msgs = self._comms.fetch()
        with _lock:
            for msg in msgs:
                key = msg.key()
                if key == "NODE_REPORT":
                    d = parse_node_report(msg.string())
                    name = d.get("NAME", "")
                    if name:
                        _vehicles[name] = {
                            "x":       float(d.get("X", 0)),
                            "y":       float(d.get("Y", 0)),
                            "depth":   float(d.get("DEP", 0)),
                            "heading": float(d.get("HDG", 0)),
                            "speed":   float(d.get("SPD", 0)),
                            "type":    d.get("TYPE", "AUV"),
                            "group":   d.get("GROUP", ""),
                            "time":    time.time(),
                        }
                elif key in ("INSPECTION_SCORE", "GAME_SCORE"):
                    _score = msg.string()
                elif key == "DEPLOY_ALL":
                    _deploy = msg.string().strip().lower() == "true"
        return True


# ---------------------------------------------------------------------------
# Flask application
# ---------------------------------------------------------------------------

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html",
                           shore_host=SHORE_HOST,
                           shore_port=SHORE_PORT)


@app.route("/api/state")
def api_state():
    now = time.time()
    with _lock:
        vehicles_out = {}
        for name, v in _vehicles.items():
            age = now - v["time"]
            vehicles_out[name] = {**v, "age_s": round(age, 1)}
        return jsonify({
            "vehicles": vehicles_out,
            "score":    _score,
            "deployed": _deploy,
            "moos_ok":  MOOS_AVAILABLE,
            "ts":       now,
        })


@app.route("/api/deploy", methods=["POST"])
def api_deploy():
    """POST to trigger DEPLOY_ALL=true on the shoreside."""
    if not MOOS_AVAILABLE or _sub is None:
        return jsonify({"ok": False, "reason": "no MOOS connection"}), 503
    _sub._comms.notify("DEPLOY_ALL", "true", -1)
    return jsonify({"ok": True})


@app.route("/api/halt", methods=["POST"])
def api_halt():
    """POST to trigger DEPLOY_ALL=false (halt all vehicles)."""
    if not MOOS_AVAILABLE or _sub is None:
        return jsonify({"ok": False, "reason": "no MOOS connection"}), 503
    _sub._comms.notify("DEPLOY_ALL", "false", -1)
    return jsonify({"ok": True})


# ---------------------------------------------------------------------------
# Startup
# ---------------------------------------------------------------------------

_sub = None

def start_moos():
    global _sub
    if not MOOS_AVAILABLE:
        print("WARNING: pymoos not available — running in demo mode (no live data).")
        return
    try:
        _sub = ShoresideSubscriber()
        print(f"Connected to shoreside MOOSDB at {SHORE_HOST}:{SHORE_PORT}")
    except Exception as e:
        print(f"WARNING: Could not connect to MOOSDB: {e}")


if __name__ == "__main__":
    t = threading.Thread(target=start_moos, daemon=True)
    t.start()
    time.sleep(1.0)  # give MOOS time to connect before first request
    print(f"Dashboard: http://0.0.0.0:{WEB_PORT}")
    app.run(host="0.0.0.0", port=WEB_PORT, debug=False)
