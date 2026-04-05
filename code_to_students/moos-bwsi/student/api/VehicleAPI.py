"""
VehicleAPI.py — Python interface for BWSI AUVC student vehicles
===============================================================

Wraps pymoos so students can write mission logic in Python without touching
C++ or the MOOS configuration files.

Quick start
-----------
    from api import VehicleAPI

    api = VehicleAPI("jellyfish", server_port=9000)
    api.start()

    while api.running:
        contacts = api.contacts()
        nearby   = [c for c in contacts if c.distance_2d(api.x, api.y) < 40]

        if nearby:
            target = min(nearby, key=lambda c: c.distance_2d(api.x, api.y))
            api.chase(target.name)
        else:
            api.loiter()

        api.sleep(0.25)

Prerequisites
-------------
pymoos must be installed on the student's machine (comes with MOOS-IvP):
    pip install pymoos        # if available as a wheel
    # or build from the MOOS-IvP source tree

The vehicle's MOOS community must be running (i.e. the mission was launched
with launch_game.sh) before you call api.start().

If your scenario uses student_mode = "python" the generated .moos file omits
pChallenge so there is no conflict.  If pChallenge is still present both
processes publish the same variables — the last write wins, which may cause
erratic behaviour; remove or comment out the pChallenge Run= line instead.
"""

from __future__ import annotations

import math
import threading
import time
from typing import Dict, List, Optional, Tuple

try:
    import pymoos
except ImportError as _e:
    raise ImportError(
        "pymoos is not installed.\n"
        "  On a machine with MOOS-IvP: pip install pymoos\n"
        "  Or build from the MOOS-IvP source tree."
    ) from _e


# ---------------------------------------------------------------------------
# Contact — one entry decoded from a NODE_REPORT string
# ---------------------------------------------------------------------------

class Contact:
    """
    Represents a single vehicle / NPC decoded from a NODE_REPORT message.

    NODE_REPORT format (comma-separated KEY=VALUE pairs):
        NAME=moby,TYPE=AUV,GROUP=npc,X=-30.1,Y=-220.5,DEP=0.0,HDG=45.0,SPD=1.8,...
    """

    def __init__(self, raw: str):
        self._fields: Dict[str, str] = {}
        for token in raw.split(","):
            if "=" in token:
                k, _, v = token.partition("=")
                self._fields[k.strip().upper()] = v.strip()
        self._raw = raw

    # ---- identity ----

    @property
    def name(self) -> str:
        return self._fields.get("NAME", "")

    @property
    def type(self) -> str:
        """Platform type string, e.g. "AUV", "USV", "SHIP"."""
        return self._fields.get("TYPE", "")

    @property
    def group(self) -> str:
        """Group / team label, e.g. "alpha", "npc"."""
        return self._fields.get("GROUP", "")

    # ---- pose ----

    @property
    def x(self) -> float:
        return self._get_float("X")

    @property
    def y(self) -> float:
        return self._get_float("Y")

    @property
    def depth(self) -> float:
        return self._get_float("DEP")

    @property
    def heading(self) -> float:
        return self._get_float("HDG")

    @property
    def speed(self) -> float:
        return self._get_float("SPD")

    # ---- geometry helpers ----

    def distance_2d(self, own_x: float, own_y: float) -> float:
        """Horizontal (XY-plane) distance from own position to this contact."""
        dx = self.x - own_x
        dy = self.y - own_y
        return math.sqrt(dx * dx + dy * dy)

    def range_3d(self, own_x: float, own_y: float, own_depth: float) -> float:
        """True slant range including depth difference."""
        dx = self.x - own_x
        dy = self.y - own_y
        dz = self.depth - own_depth
        return math.sqrt(dx * dx + dy * dy + dz * dz)

    # ---- internals ----

    def _get_float(self, key: str, default: float = 0.0) -> float:
        try:
            return float(self._fields[key])
        except (KeyError, ValueError):
            return default

    def __repr__(self) -> str:
        return (f"Contact(name={self.name!r}, type={self.type!r}, "
                f"group={self.group!r}, x={self.x:.1f}, y={self.y:.1f}, "
                f"depth={self.depth:.1f})")


# ---------------------------------------------------------------------------
# VehicleAPI — the main student-facing class
# ---------------------------------------------------------------------------

class VehicleAPI:
    """
    Python interface to one BWSI AUVC vehicle MOOS community.

    Parameters
    ----------
    vehicle_name : str
        Name of your vehicle, e.g. "jellyfish".  Must match the community
        name in the generated .moos file.
    server_port : int
        MOOSDB port for this vehicle (from the scenario; default 9000 for the
        first vehicle, 9001 for the second, etc.).
    server_host : str
        Host running MOOSDB (default "localhost").
    app_name : str
        Name this process registers as in MOOS (visible in uProcessWatch /
        appcast panel).  Defaults to "pStudent_<vehicle_name>".
    start_x, start_y : float
        Starting position of your vehicle (optional).  Used by
        return_to_base() if set.
    """

    def __init__(
        self,
        vehicle_name: str,
        server_port: int = 9000,
        server_host: str = "localhost",
        app_name: Optional[str] = None,
        start_x: float = 0.0,
        start_y: float = 0.0,
    ):
        self._vehicle_name = vehicle_name
        self._server_port  = server_port
        self._server_host  = server_host
        self._app_name     = app_name or f"pStudent_{vehicle_name}"

        # Own pose (updated from MOOS)
        self._lock    = threading.Lock()
        self._x       = 0.0
        self._y       = 0.0
        self._depth   = 0.0
        self._heading = 0.0
        self._speed   = 0.0
        self._deployed = False

        # Contact registry: name → Contact
        self._contacts: Dict[str, Contact] = {}

        # Collected contacts (locally tracked by student code)
        self._collected: set = set()

        # Base / return position
        self._base_x = start_x
        self._base_y = start_y

        # Runtime state
        self._running  = False
        self._comms: Optional[pymoos.comms] = None
        self._thread: Optional[threading.Thread] = None

    # ------------------------------------------------------------------
    # Connection lifecycle
    # ------------------------------------------------------------------

    def start(self, timeout: float = 10.0) -> None:
        """
        Connect to the MOOS community and start receiving messages.

        Blocks until the connection is established or *timeout* seconds
        have elapsed.  Raises RuntimeError on failure.
        """
        self._comms = pymoos.comms()
        self._comms.set_on_connect_callback(self._on_connect)
        self._comms.set_on_new_mail_callback(self._on_new_mail)

        self._comms.run(self._server_host, self._server_port, self._app_name)

        deadline = time.time() + timeout
        while time.time() < deadline:
            if self._comms.is_connected():
                self._running = True
                return
            time.sleep(0.1)

        raise RuntimeError(
            f"Could not connect to MOOS community '{self._vehicle_name}' at "
            f"{self._server_host}:{self._server_port} within {timeout}s.\n"
            "Is the mission running?  Check: pAntler <vehicle>.moos"
        )

    def stop(self) -> None:
        """Disconnect from MOOS."""
        self._running = False
        if self._comms:
            self._comms.close(True)

    @property
    def running(self) -> bool:
        """True while connected and the mission DEPLOY flag is true."""
        return self._running and self._deployed

    def sleep(self, seconds: float) -> None:
        """
        Convenience wrapper for time.sleep().

        Prefer this over time.sleep() directly so that future versions can
        account for MOOS time warp.
        """
        time.sleep(seconds)

    # ------------------------------------------------------------------
    # Own vehicle state
    # ------------------------------------------------------------------

    @property
    def x(self) -> float:
        """Own X position in metres from origin."""
        with self._lock:
            return self._x

    @property
    def y(self) -> float:
        """Own Y position in metres from origin."""
        with self._lock:
            return self._y

    @property
    def depth(self) -> float:
        """Own depth in metres (positive downward)."""
        with self._lock:
            return self._depth

    @property
    def heading(self) -> float:
        """Own heading in degrees (0 = north, clockwise)."""
        with self._lock:
            return self._heading

    @property
    def speed(self) -> float:
        """Own speed in m/s."""
        with self._lock:
            return self._speed

    @property
    def deployed(self) -> bool:
        """True when the DEPLOY flag is set (mission active)."""
        with self._lock:
            return self._deployed

    @property
    def position(self) -> Tuple[float, float]:
        """Own (x, y) as a tuple."""
        with self._lock:
            return self._x, self._y

    # ------------------------------------------------------------------
    # Contact management
    # ------------------------------------------------------------------

    def contacts(self) -> List[Contact]:
        """
        Return a snapshot of all known contacts (including NPCs).

        The list updates automatically as NODE_REPORT messages arrive.
        Filter by group to separate teams from NPCs:

            players = [c for c in api.contacts() if c.group != "npc"]
            npcs    = [c for c in api.contacts() if c.group == "npc"]
        """
        with self._lock:
            return list(self._contacts.values())

    def get_contact(self, name: str) -> Optional[Contact]:
        """Return the most recent Contact with the given name, or None."""
        with self._lock:
            return self._contacts.get(name)

    def mark_collected(self, contact: Contact) -> None:
        """
        Record that *contact* has been handled (e.g. whale tagged, fish
        photographed).  Collected contacts are filtered out by
        uncollected_contacts().
        """
        self._collected.add(contact.name)

    def is_collected(self, contact: Contact) -> bool:
        """True if mark_collected() has been called for this contact."""
        return contact.name in self._collected

    def uncollected_contacts(self) -> List[Contact]:
        """Contacts that have not yet been marked as collected."""
        with self._lock:
            return [c for c in self._contacts.values()
                    if c.name not in self._collected]

    # ------------------------------------------------------------------
    # Motion commands
    # ------------------------------------------------------------------

    def chase(self, contact_name: str) -> None:
        """
        Chase the named contact using BHV_CutRange.

        Sets CLOSE=true and CHASE_UPDATES=contact=<name>.
        """
        self.notify("CHASE_UPDATES", f"contact={contact_name}")
        self.notify("CLOSE",  "true")
        self.notify("LOITER", "false")

    def loiter(self) -> None:
        """
        Resume the default patrol loiter (BHV_Loiter polygon from the .bhv
        file).

        Sets CLOSE=false and LOITER=true.
        """
        self.notify("CLOSE",  "false")
        self.notify("LOITER", "true")

    def loiter_at(self, x: float, y: float, radius: float = 15.0,
                  speed: float = 1.5) -> None:
        """
        Loiter around a specific (x, y) point.

        Sends a LOITER_UPDATES message to move BHV_Loiter's centre.
        """
        update = f"center_assign=x={x:.1f},y={y:.1f},radius={radius:.1f},speed={speed:.1f}"
        self.notify("LOITER_UPDATES", update)
        self.notify("CLOSE",  "false")
        self.notify("LOITER", "true")

    def go_to(self, x: float, y: float, speed: float = 1.5) -> None:
        """
        Drive to a waypoint using BHV_Waypoint.

        Requires BHV_Waypoint to be present in the vehicle's .bhv file
        (included by default when student_mode = "python" is set in the
        scenario TOML).

        Publishes WPT_UPDATE = "points=x,y" and sets GO_TO=true.
        """
        self.notify("WPT_UPDATE", f"points={x:.1f},{y:.1f},speed={speed:.1f}")
        self.notify("CLOSE",  "false")
        self.notify("LOITER", "false")
        self.notify("GO_TO",  "true")

    def go_to_sequence(self, waypoints: List[Tuple[float, float]],
                       speed: float = 1.5, repeat: bool = False) -> None:
        """
        Follow a sequence of (x, y) waypoints.

        Parameters
        ----------
        waypoints : list of (x, y) tuples
        speed     : transit speed in m/s
        repeat    : if True, cycle through the list indefinitely
        """
        pts = ":".join(f"{x:.1f},{y:.1f}" for x, y in waypoints)
        update = f"points={pts},speed={speed:.1f}"
        if repeat:
            update += ",cyclic_point=1"
        self.notify("WPT_UPDATE", update)
        self.notify("CLOSE",  "false")
        self.notify("LOITER", "false")
        self.notify("GO_TO",  "true")

    def return_to_base(self, speed: float = 1.5) -> None:
        """
        Drive back to the vehicle's starting position (set at construction
        time or via set_base()).
        """
        self.go_to(self._base_x, self._base_y, speed=speed)

    def set_base(self, x: float, y: float) -> None:
        """Override the base position used by return_to_base()."""
        self._base_x = x
        self._base_y = y

    def halt(self) -> None:
        """
        Stop active commands (cancel chase, cancel go_to, cancel loiter).

        Switches the helm to Inactive by publishing DEPLOY=false — use with
        caution.  Call loiter() to resume.
        """
        self.notify("CLOSE",  "false")
        self.notify("LOITER", "false")
        self.notify("GO_TO",  "false")

    # ------------------------------------------------------------------
    # Low-level MOOS access
    # ------------------------------------------------------------------

    def notify(self, var: str, value) -> None:
        """
        Publish a MOOS variable.

        value may be a str, int, or float.  Strings are published as string
        messages; numbers as double messages.
        """
        if self._comms is None:
            raise RuntimeError("Not connected — call start() first.")
        if isinstance(value, (int, float)):
            self._comms.notify(var, float(value), pymoos.time())
        else:
            self._comms.notify(var, str(value), pymoos.time())

    # ------------------------------------------------------------------
    # Internal MOOS callbacks
    # ------------------------------------------------------------------

    def _on_connect(self) -> bool:
        """Subscribe to all variables we need on connect / reconnect."""
        c = self._comms
        c.register("NAV_X",       0)
        c.register("NAV_Y",       0)
        c.register("NAV_DEPTH",   0)
        c.register("NAV_HEADING", 0)
        c.register("NAV_SPEED",   0)
        c.register("DEPLOY",      0)
        c.register("NODE_REPORT", 0)
        return True

    def _on_new_mail(self, messages) -> bool:
        """Process incoming MOOS mail."""
        with self._lock:
            for msg in messages:
                key = msg.key()
                if key == "NAV_X":
                    self._x = msg.double()
                elif key == "NAV_Y":
                    self._y = msg.double()
                elif key == "NAV_DEPTH":
                    self._depth = msg.double()
                elif key == "NAV_HEADING":
                    self._heading = msg.double()
                elif key == "NAV_SPEED":
                    self._speed = msg.double()
                elif key == "DEPLOY":
                    raw = msg.string().strip().lower()
                    self._deployed = raw == "true"
                elif key == "NODE_REPORT":
                    contact = Contact(msg.string())
                    # Don't add ourselves to the contact list
                    if contact.name and contact.name != self._vehicle_name:
                        self._contacts[contact.name] = contact
        return True
