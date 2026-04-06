# Decision-Making Under Uncertainty for Marine Autonomy

This guide explains how to build robust autonomy logic for underwater (UUV) and
surface (USV) vehicles.  Real ocean missions are full of uncertainty: sensors
are noisy, GPS is unavailable while submerged, contacts drift out of detection
range, and your vehicle cannot stop or turn on a dime.  The patterns below help
you reason correctly despite that uncertainty.

---

## Contents

1. [Sources of Uncertainty](#1-sources-of-uncertainty)
2. [Sensor Models and ROC Curves](#2-sensor-models-and-roc-curves)
3. [Bayesian Belief Updating](#3-bayesian-belief-updating)
4. [Platform Dynamics](#4-platform-dynamics)
5. [Contact Prediction and Staleness](#5-contact-prediction-and-staleness)
6. [Collision Avoidance Under Uncertainty](#6-collision-avoidance-under-uncertainty)
7. [Planning Under Uncertainty (POMDP)](#7-planning-under-uncertainty-pomdp)
8. [Practical Decision Patterns](#8-practical-decision-patterns)
9. [IvP Multi-Objective Framing](#9-ivp-multi-objective-framing)
10. [Code Reference](#10-code-reference)

---

## 1. Sources of Uncertainty

Every autonomous marine vehicle deals with three kinds of uncertainty:

| Kind | Where it comes from | Example |
|------|--------------------|---------| 
| **Sensor uncertainty** | Noise in range/bearing measurements; missed detections; false alarms | Acoustic beacon range ±2 m; sonar misses at 28 m |
| **Navigation uncertainty** | Dead-reckoning error accumulates without GPS | AUV position drifts ~5% of distance travelled per minute |
| **Contact uncertainty** | Other vehicles move; NODE_REPORT may be stale | Contact was at (−50, −120) two seconds ago — where is it now? |

The key insight is that your vehicle should track a **belief** — a probability
distribution over possible world states — rather than treating the most recent
measurement as ground truth.

---

## 2. Sensor Models and ROC Curves

Every sensor has a characteristic trade-off between **probability of detection**
(P_D) and **probability of false alarm** (P_FA).  Plotting P_D vs P_FA as the
decision threshold varies gives the **Receiver Operating Characteristic (ROC)**
curve.

```
P_D
 1 |          *****
   |      ****
   |    **
   |   *
   |  *
   | *
   |*
 0 +-------------- P_FA
   0                1
```

An ideal sensor sits at (0, 1) — never false-alarming, never missing.  A
random guesser follows the diagonal.

### Linear range-falloff model

`pInfrastructureSensor` uses a simple linear model:

```
P_D(range) = max(0,  1 − range / detect_range)
```

Detection messages include a `confidence` field equal to the P_D value used:

```
pipeline=cable_01,x=-101.2,y=-179.5,type=anomaly,
anomaly_type=damage,range=12.4,confidence=0.587
```

Use this field to **weight** incoming observations — a detection at 5 m is more
trustworthy than one at 28 m.

### Beacon range noise

`uFldBeaconRangeSensor` adds uniform noise ±`rn_uniform_magnitude` (default 2 m):

```
measured_range = true_range + Uniform(−N, +N)
```

When trilaterating, propagate this uncertainty through the geometry (see §7).

---

## 3. Bayesian Belief Updating

### Log-odds representation

Track the presence/absence of a feature (anomaly, target, hazard) using a
**log-odds score** `L`:

```
L  =  log( P(feature present) / P(feature absent) )
```

| L value | Meaning |
|---------|---------|
| 0 | Completely uncertain (50/50) |
| +4 | ~98% confident present |
| −4 | ~98% confident absent |

### Update rule

On a **positive detection** (sensor fires):
```
L  +=  log( P_D / P_FA )
```

On a **negative observation** (sensor did not fire when it could have):
```
L  −=  log( (1 − P_D) / (1 − P_FA) )
```

Convert back to probability:
```
P  =  exp(L) / (1 + exp(L))
```

### C++ — BeliefState

`libBWSI` provides `BeliefState` for this calculation:

```cpp
#include "BeliefState.h"

BeliefState belief;           // starts at L=0 (50% prior)

// Each time the sonar fires on an anomaly candidate
belief.updatePositive(0.7, 0.02);   // P_D=0.7, P_FA=0.02
// Each time the sonar could see it but did not detect anything
belief.updateNegative(0.7, 0.02);

double prob = belief.probability();       // current P(anomaly present)
bool   confirmed = belief.decision(0.9); // true when P >= 0.90

// Decay belief when the vehicle moves away (sensor no longer observing)
belief.decay(0.95);                       // multiply L by 0.95 each tick

// Reset for a new candidate
belief.reset();
```

### Python — DetectionBuffer

```python
from api import DetectionBuffer

buf = DetectionBuffer(pd=0.7, pfa=0.02, decay=0.95)

# Receive a detection message from pInfrastructureSensor
buf.update_positive()

# The sensor was in range but saw nothing at this step
buf.update_negative()

# Periodic decay
buf.tick_decay()

if buf.decision(threshold=0.85):
    print(f"Anomaly confirmed! P = {buf.probability():.2f}")
```

### Practical thresholds

| Decision | Suggested threshold |
|----------|-------------------|
| Start investigating | P > 0.5 |
| Report anomaly | P > 0.85 |
| Mark as false alarm and discard | P < 0.10 after N steps |

These values trade off detection rate against false-alarm rate — exactly the
ROC curve.  Tuning the threshold moves your operating point along the curve.

---

## 4. Platform Dynamics

Your vehicle is not a point mass.  Understanding its physical constraints
makes your autonomy far more robust.

### Turn radius

At speed `v` (m/s) with a maximum turn rate `u` (deg/s):

```
r = v / ( (u / 180) × π )
```

A vehicle doing 2 m/s with a 20 deg/s turn rate needs a **5.7 m** radius to
complete a turn.  This matters when chasing fast contacts or threading narrow
corridors.

| Speed (m/s) | Turn rate (deg/s) | Min turn radius (m) |
|-------------|-------------------|---------------------|
| 1.0 | 20 | 2.9 |
| 2.0 | 20 | 5.7 |
| 2.0 | 10 | 11.5 |
| 3.0 | 15 | 11.5 |

**Consequence**: if a contact is inside your turn radius, you cannot intercept
it by pointing directly at it.  Use the `BHV_CutRange` behavior, which already
accounts for this, or plan a curved approach.

### Underactuated dynamics

AUVs are typically **underactuated**: they can control surge (forward speed)
and yaw (heading), but not sway (sideways) directly.  At low speed the vehicle
is highly manoeuvrable; at high speed it becomes more like an aircraft and
requires wide arcs.

For depth control, `BHV_ConstantDepth` handles the pitch loop.  If you want
to drive depth directly in your logic, publish:

```cpp
Notify("DEPTH_UPDATES", "depth=" + doubleToString(newDepth));
```

### Speed vs. maneuverability trade-off

Moving fast covers ground quickly but reduces turn authority and increases
acoustic noise (harder for the sensor model to detect things).  A good rule of
thumb:

- **Survey/inspection**: 1.0–1.5 m/s (tight turns, high detection probability)
- **Transit/chase**: 2.0–3.0 m/s (cover ground fast, wider turns)

---

## 5. Contact Prediction and Staleness

When a contact's NODE_REPORT is old, its actual position is unknown.  Use
dead-reckoning to estimate where it is now:

```cpp
// In C++, ContactTracker provides:
double age  = _tracker.contactAge("moby");          // seconds since last report
double conf = _tracker.contactConfidence("moby", 5.0); // 0→1, half-life 5 s

// Predict position assuming constant heading and speed:
auto [px, py] = _tracker.predictPosition("moby", age);
```

```python
# In Python, Contact is always the last received position.
# Predict manually:
import math
dt = time.time() - c._last_seen   # you can add this field to VehicleAPI
px = c.x + c.speed * math.sin(math.radians(c.heading)) * dt
py = c.y + c.speed * math.cos(math.radians(c.heading)) * dt
```

### Confidence decay

Confidence decays exponentially with contact age:

```
confidence(age) = exp(−age × ln2 / half_life)
```

At one half-life the confidence is 50%; at two half-lives it is 25%.  Use
this to decide when to abandon a chase:

```cpp
if (_tracker.contactConfidence(target.name(), 8.0) < 0.2) {
    // Lost track — fall back to loiter
    Notify("CLOSE",  "false");
    Notify("LOITER", "true");
}
```

---

## 6. Collision Avoidance Under Uncertainty

### CPA geometry

The **Closest Point of Approach (CPA)** is the minimum distance two vehicles
will reach if neither changes course.

Key quantities:
- **DCPA** — Distance at CPA (m).  If DCPA < collision_radius → danger.
- **TCPA** — Time to CPA (s).  If negative → already past, threat receding.

```cpp
// Pseudo-code: compute DCPA/TCPA for a contact
double dvx = contact.speed() * sin(hdgRad) - _speed * sin(_hdgRad);
double dvy = contact.speed() * cos(hdgRad) - _speed * cos(_hdgRad);
double drx = contact.x() - _navX;
double dry = contact.y() - _navY;

double dvdv = dvx*dvx + dvy*dvy;
double tcpa = (dvdv > 1e-6) ? -(drx*dvx + dry*dvy) / dvdv : 1e9;
double dcpa = sqrt(max(0.0, (drx + dvx*tcpa)*(drx + dvx*tcpa) +
                             (dry + dvy*tcpa)*(dry + dvy*tcpa)));
```

`BHV_AvoidCollision` computes this internally.  If you want to act early on a
dangerous contact (e.g., a shark), check DCPA/TCPA yourself and switch modes
before the behavior fires.

### Velocity Obstacles under uncertainty

In the presence of position uncertainty σ, the safe region shrinks.  Inflate
the obstacle's collision radius by the **Minkowski sum** of the uncertainty
ellipses:

```
r_safe  =  r_vehicle + r_contact + kσ
```

where `k = 2` gives ~95% safety (2σ bound).  Use this inflated radius when
evaluating DCPA — if DCPA < r_safe, take evasive action even though the
nominal path might not collide.

```cpp
double sigma = _tracker.contactConfidence(c.name(), 5.0) < 0.5 ?
               5.0 : 2.0;   // larger uncertainty for stale contacts
double rSafe  = 5.0 + 5.0 + 2.0 * sigma;   // collision radius + uncertainty

if (dcpa < rSafe && tcpa > 0 && tcpa < 30.0) {
    // Take evasive action
    Notify("LOITER", "true");
    Notify("CLOSE",  "false");
}
```

---

## 7. Planning Under Uncertainty (POMDP)

A **Partially Observable Markov Decision Process (POMDP)** is the formal
framework for decision-making when you cannot observe the full state.

### Core concepts

| Term | Meaning |
|------|---------|
| **State** *s* | True world state (your position, contact positions, anomaly locations) |
| **Belief** *b* | Probability distribution over states — what you think is true |
| **Action** *a* | What you do (chase, loiter, go_to, surface) |
| **Observation** *o* | What sensors return (node reports, detections, beacon ranges) |
| **Reward** *r(s,a)* | Score for taking action *a* in state *s* |

The POMDP policy maps beliefs to actions: `π(b) → a`.

### Online solvers (for reference)

Full POMDP solvers are complex to implement from scratch.  These online
solvers are practical for real-time robotics:

| Solver | Approach | When to use |
|--------|----------|-------------|
| **POMCP** | Monte Carlo tree search in belief space | Continuous states, real-time |
| **DESPOT** | Determinised scenario trees | Large state spaces |
| **STRUG** | Anytime with GPU support | Multi-vehicle coordination |

For the BWSI challenge, you don't need a full POMDP solver.  The practical
patterns in §8 capture most of the benefit.

### Belief Roadmap (BRM)

A **Belief Roadmap** extends a sampling-based path planner (like RRT or PRM)
to operate in **belief space** rather than configuration space.  Each node is
a Gaussian belief `b = (μ, Σ)` — a mean position plus covariance.

An Extended Kalman Filter (EKF) propagates the belief along edges:

```
μ_{t+1}  =  f(μ_t, a_t)              # motion model
Σ_{t+1}  =  F Σ_t Fᵀ + Q            # covariance prediction
K        =  Σ_t Hᵀ (H Σ_t Hᵀ + R)⁻¹ # Kalman gain
μ_{t+1}  +=  K (z_{t+1} − h(μ_{t+1}))
Σ_{t+1}  =  (I − KH) Σ_{t+1}         # covariance update
```

Where:
- `F` = Jacobian of motion model
- `Q` = process noise covariance
- `H` = Jacobian of observation model
- `R` = sensor noise covariance
- `z` = actual measurement

For the GPS-denied scenario, use beacon ranges as `z`, and the beacon
positions as the observation model `h(μ)` (distance from estimated position
to each beacon).

### Chance-constrained planning

Instead of minimising expected cost, **chance-constrained** planning enforces
that constraints are satisfied with high probability:

```
P( collision ) ≤ δ          (e.g. δ = 0.05  →  95% safe)
P( coverage complete ) ≥ γ  (e.g. γ = 0.80)
```

You can approximate this by propagating a Gaussian state distribution forward
in time and checking whether the 2σ ellipse overlaps forbidden regions.

---

## 8. Practical Decision Patterns

These patterns capture most of the robustness benefits of full POMDP planning
with much simpler implementation.

### Pattern 1 — Hysteresis

Prevent mode-chattering by requiring the trigger condition to hold for several
consecutive iterations before switching modes.

```cpp
// In Challenge.h:
int _chaseConfirmCount = 0;
static const int CHASE_CONFIRM_REQUIRED = 3;

// In Challenge::Iterate():
if (shouldChase) {
    _chaseConfirmCount++;
    if (_chaseConfirmCount >= CHASE_CONFIRM_REQUIRED) {
        Notify("CLOSE", "true");
        Notify("LOITER", "false");
    }
} else {
    _chaseConfirmCount = 0;
    Notify("CLOSE", "false");
    Notify("LOITER", "true");
}
```

```python
# Python equivalent
chase_ticks = 0
CHASE_REQUIRED = 3

while api.running:
    if should_chase(target):
        chase_ticks += 1
        if chase_ticks >= CHASE_REQUIRED:
            api.chase(target.name)
    else:
        chase_ticks = 0
        api.loiter()
    api.sleep(0.25)
```

### Pattern 2 — Sequential Probability Ratio Test (SPRT)

The SPRT is the optimal statistical test for deciding between two hypotheses
(H₀: no anomaly, H₁: anomaly) with a fixed error budget.  Stop as soon as
sufficient evidence is accumulated:

```python
import math

# SPRT thresholds
ALPHA = 0.05   # max false-alarm rate
BETA  = 0.10   # max miss rate

LOG_UPPER = math.log((1 - BETA) / ALPHA)   # accept H1
LOG_LOWER = math.log(BETA / (1 - ALPHA))   # accept H0

log_ratio = 0.0
PD, PFA = 0.7, 0.02

for detection in incoming_detections:
    if detection.type == "anomaly":
        log_ratio += math.log(PD / PFA)
    else:
        log_ratio += math.log((1 - PD) / (1 - PFA))

    if log_ratio >= LOG_UPPER:
        report_anomaly(detection)
        break
    elif log_ratio <= LOG_LOWER:
        discard_candidate()
        break
```

### Pattern 3 — Confidence-gated actions

Only take high-stakes actions (surfacing, reporting, committing to a course)
when belief exceeds a high threshold.  Use a lower threshold to start
gathering information.

```python
buf = DetectionBuffer(pd=0.7, pfa=0.02)

# Stage 1: start paying attention
if buf.probability() > 0.4:
    api.loiter_at(candidate_x, candidate_y, radius=10)

# Stage 2: commit to reporting
if buf.probability() > 0.85:
    api.notify("ANOMALY_REPORT_JELLYFISH",
               f"pipeline={pipeline},x={cx:.1f},y={cy:.1f},"
               f"type=anomaly,anomaly_type={atype},count={count}")
    buf.reset()
```

### Pattern 4 — Mode with timer fallback

Never get stuck in a mode indefinitely.  Always include a maximum duration:

```cpp
// In Challenge.h:
double _modeStartTime = 0.0;
std::string _currentMode = "loiter";
static constexpr double MAX_CHASE_SECONDS = 60.0;

// In Challenge::Iterate():
double now = MOOSTime();

if (_currentMode == "chase") {
    if (now - _modeStartTime > MAX_CHASE_SECONDS) {
        // Give up — lost the contact or can't close
        _currentMode = "loiter";
        Notify("CLOSE", "false");
        Notify("LOITER", "true");
    }
}
```

### Pattern 5 — Priority queue over contacts

When multiple targets are in range, rank them explicitly rather than choosing
the nearest one blindly.  Combine distance, belief confidence, and mission
priority:

```python
def score_contact(c, api, belief_map):
    priority  = {"treasure": 4, "whale": 3, "fish": 2}.get(c.type.lower(), 0)
    dist      = c.distance_2d(api.x, api.y)
    conf      = belief_map.get(c.name, 0.5)   # how sure we are it's there
    age_penalty = min(1.0, (time.time() - c._last_seen) / 10.0)

    return priority * conf - 0.01 * dist - age_penalty

candidates = [c for c in api.contacts()
              if c.group == "npc" and c.type.lower() != "shark"
              and not api.is_collected(c)]

if candidates:
    target = max(candidates, key=lambda c: score_contact(c, api, beliefs))
    api.chase(target.name)
```

---

## 9. IvP Multi-Objective Framing

MOOS-IvP's Interval Programming (IvP) solver is already a sophisticated
decision-maker.  Each behavior defines a **utility function** over (course,
speed) space; the solver finds the action that maximises the weighted sum of
all active utilities.

You don't need to implement IvP from scratch — but understanding it helps you
tune behavior priorities:

```
Behavior priority weights (higher = more influence):
  BHV_OpRegion      100   ← hard boundary (very high weight)
  BHV_AvoidCollision 80   ← collision avoidance
  BHV_CutRange       50   ← chase
  BHV_Waypoint       50   ← go_to
  BHV_Loiter         30   ← patrol (lowest normal priority)
```

You can change these in the `.bhv` file's `priority` field.  Avoid setting
navigation-safety behaviors lower than mission behaviors.

The IvP Helm selects the globally optimal action across ALL active behaviors
simultaneously — this is fundamentally different from a priority list that
would simply override lower-priority behaviors entirely.

---

## 10. Code Reference

### C++ — BeliefState

```cpp
#include "BeliefState.h"

BeliefState b;
b.updatePositive(double pd, double pfa);  // positive detection
b.updateNegative(double pd, double pfa);  // null observation
b.decay(double alpha);                    // multiply L by alpha (0 < α ≤ 1)
b.reset();                                // back to L=0
double b.logOdds();                       // current L
double b.probability();                   // P = sigmoid(L)
bool   b.decision(double threshold=0.9);  // true when P >= threshold
```

### C++ — ContactTracker (uncertainty extensions)

```cpp
// Seconds since the last NODE_REPORT for this contact name.
double age = _tracker.contactAge("moby");

// Exponential-decay confidence: 1.0 when fresh, 0.0 when stale.
// half_life is the time (s) at which confidence = 0.5
double conf = _tracker.contactConfidence("moby", 5.0);

// Dead-reckoning position estimate at +dt seconds.
auto [px, py] = _tracker.predictPosition("moby", dt);
```

### Python — DetectionBuffer

```python
from api import DetectionBuffer

buf = DetectionBuffer(pd=0.7, pfa=0.02, decay=0.98)
buf.update_positive()        # sensor fired
buf.update_negative()        # sensor could see this area but did not fire
buf.tick_decay()             # call once per loop iteration
buf.reset()                  # clear belief

buf.log_odds()               # float — current L
buf.probability()            # float in [0, 1]
buf.decision(threshold=0.85) # bool
```

### Python — Contact timestamp

The Python `Contact` class stores a `last_seen` float (Unix time) for
staleness checks:

```python
import time
age  = time.time() - c.last_seen   # seconds since last NODE_REPORT
conf = math.exp(-age * math.log(2) / half_life)
```

---

## Further Reading

- Benjamin et al., "MOOS-IvP and a Mission Autonomy Protocol" — IvP Helm design
- Kaelbling et al., "Planning and acting in partially observable stochastic domains" — POMDP theory
- Silver & Veness, "Monte-Carlo Planning in Large POMDPs" — POMCP algorithm
- Bahr et al., "Consistent Cooperative Localization" — acoustic beacon navigation
- Kuwata et al., "Real-time Motion Planning with Applications to Autonomous Urban Driving" — CPA geometry
