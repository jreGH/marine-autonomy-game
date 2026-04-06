/************************************************************/
/*    FILE: ContactTracker.cpp                              */
/*    ORGN: BWSI AUVC                                       */
/************************************************************/
#include "ContactTracker.h"
#include <cmath>
#include <limits>

// Use wall-clock time for contact age tracking.
// In a MOOS process, replace with MOOSTime() if preferred.
#include <chrono>

static double nowSeconds() {
  using namespace std::chrono;
  return duration<double>(steady_clock::now().time_since_epoch()).count();
}

ContactTracker::ContactTracker() : _emptyCount(0) {}

bool ContactTracker::processReport(const std::string& rawReport) {
  NodeReport r = NodeReport::fromString(rawReport);
  if (!r.valid())
    return false;

  _lastSeenTime[r.name()] = nowSeconds();

  for (NodeReport& c : _contacts) {
    if (c.sameContact(r)) {
      c = r;  // update in place
      return true;
    }
  }
  _contacts.push_back(r);
  return true;
}

void ContactTracker::markCollected(const NodeReport& contact) {
  for (const NodeReport& c : _collected) {
    if (c.sameContact(contact))
      return;  // already marked
  }
  _collected.push_back(contact);
}

bool ContactTracker::isCollected(const NodeReport& contact) const {
  for (const NodeReport& c : _collected) {
    if (c.sameContact(contact))
      return true;
  }
  return false;
}

int ContactTracker::tickEmpty() {
  return ++_emptyCount;
}

void ContactTracker::tickReceived() {
  _emptyCount = 0;
}

// ---------------------------------------------------------------------------
// Uncertainty helpers
// ---------------------------------------------------------------------------

double ContactTracker::contactAge(const std::string& name) const {
  auto it = _lastSeenTime.find(name);
  if (it == _lastSeenTime.end())
    return -1.0;
  return nowSeconds() - it->second;
}

double ContactTracker::contactConfidence(const std::string& name,
                                         double half_life) const {
  double age = contactAge(name);
  if (age < 0.0)
    return 0.0;
  if (half_life <= 0.0)
    return (age == 0.0) ? 1.0 : 0.0;
  return std::exp(-age * std::log(2.0) / half_life);
}

std::pair<double, double> ContactTracker::predictPosition(
    const std::string& name, double dt) const {
  const double nan = std::numeric_limits<double>::quiet_NaN();

  for (const NodeReport& c : _contacts) {
    if (c.name() == name) {
      // Convert heading (0=north, clockwise) to standard math angle
      double hdgRad = c.heading() * M_PI / 180.0;
      double px = c.x() + c.speed() * std::sin(hdgRad) * dt;
      double py = c.y() + c.speed() * std::cos(hdgRad) * dt;
      return {px, py};
    }
  }
  return {nan, nan};
}
