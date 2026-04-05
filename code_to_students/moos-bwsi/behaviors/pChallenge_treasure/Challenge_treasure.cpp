/************************************************************/
/*    FILE: Challenge_treasure.cpp                          */
/*    ORGN: BWSI AUVC                                       */
/************************************************************/
#include "Challenge_treasure.h"
#include "MBUtils.h"
#include <cmath>
#include <sstream>

using namespace std;

Challenge_treasure::Challenge_treasure()
  : _myName("treasure"),
    _minChaseDist(5.0),
    _boundaryRadius(1500.0),
    _navX(0), _navY(0), _navDepth(0),
    _isPickedUp(false),
    _isCollected(false)
{}

bool Challenge_treasure::OnNewMail(MOOSMSG_LIST& NewMail) {
  AppCastingMOOSApp::OnNewMail(NewMail);

  bool gotReport = false;
  for (CMOOSMsg& msg : NewMail) {
    const string& key = msg.GetKey();
    if      (key == "NAV_X")     _navX     = msg.GetDouble();
    else if (key == "NAV_Y")     _navY     = msg.GetDouble();
    else if (key == "NAV_DEPTH") _navDepth = msg.GetDouble();
    else if (key == "NODE_REPORT" || key == "NODE_REPORT_LOCAL") {
      _tracker.processReport(msg.GetString());
      gotReport = true;
    }
  }

  if (gotReport) _tracker.tickReceived();
  else           _tracker.tickEmpty();

  return true;
}

bool Challenge_treasure::OnConnectToServer() {
  RegisterVariables();
  return true;
}

bool Challenge_treasure::Iterate() {
  AppCastingMOOSApp::Iterate();

  if (_isCollected) {
    AppCastingMOOSApp::PostReport();
    return true;
  }

  // Check whether the treasure has been carried out of the arena
  const double distFromOrigin = std::sqrt(_navX * _navX + _navY * _navY);
  if (_isPickedUp && distFromOrigin > _boundaryRadius) {
    // Find who is carrying us (the most-recently added carrier in collected list)
    const NodeReport& carrier = _tracker.contacts().front(); // best we can do
    ostringstream evt;
    evt << "SRC="    << carrier.name()
        << ",TYPE="  << carrier.type()
        << ",GROUP=" << carrier.group()
        << ",TREASURE=" << _myName;
    Notify("TREASURE_RECOVERED", evt.str());
    Notify("DEPLOY", "false");
    Notify("FOLLOW", "false");
    Notify("WAIT",   "true");
    _isCollected = true;
    AppCastingMOOSApp::PostReport();
    return true;
  }

  for (const NodeReport& contact : _tracker.contacts()) {
    const double range3D = contact.rangeTo3D(_navX, _navY, _navDepth);

    if (range3D < (2.0 * _minChaseDist)) {
      if (!_tracker.isCollected(contact)) {
        // First vehicle to reach us: pick-up event
        ostringstream evt;
        evt << "SRC="    << contact.name()
            << ",TYPE="  << contact.type()
            << ",GROUP=" << contact.group()
            << ",TREASURE=" << _myName;
        Notify("TREASURE_FOUND", evt.str());
        Notify("FOLLOW",         "true");
        Notify("WAIT",           "false");
        Notify("FOLLOW_UPDATES", "contact=" + contact.name());
        _carrierName = contact.name();
        _tracker.markCollected(contact);
        _isPickedUp = true;
      }
      else if (_isPickedUp && contact.name() != _carrierName) {
        // A different vehicle has come into range — treasure is being stolen
        Notify("FOLLOW_UPDATES", "contact=" + contact.name());
        ostringstream stolen;
        stolen << contact.name() << "," << contact.type() << "," << contact.group();
        Notify("STOLEN_BY", stolen.str());
        _tracker.markCollected(contact);
        _carrierName = contact.name();
      }
    }
  }

  AppCastingMOOSApp::PostReport();
  return true;
}

bool Challenge_treasure::OnStartUp() {
  AppCastingMOOSApp::OnStartUp();

  list<string> sParams;
  m_MissionReader.EnableVerbatimQuoting(false);
  if (m_MissionReader.GetConfiguration(GetAppName(), sParams)) {
    for (string& line : sParams) {
      string param = tolower(biteStringX(line, '='));
      string value = line;
      if      (param == "name")            _myName         = value;
      else if (param == "min_chase_dist")  _minChaseDist   = stod(value);
      else if (param == "boundary_radius") _boundaryRadius = stod(value);
    }
  }

  RegisterVariables();
  return true;
}

void Challenge_treasure::RegisterVariables() {
  AppCastingMOOSApp::RegisterVariables();
  Register("NAV_X",             0);
  Register("NAV_Y",             0);
  Register("NAV_DEPTH",         0);
  Register("NODE_REPORT",       0);
  Register("NODE_REPORT_LOCAL", 0);
}

bool Challenge_treasure::buildReport() {
  string stateStr = "WAITING";
  if      (_isCollected) stateStr = "COLLECTED";
  else if (_isPickedUp)  stateStr = "FOLLOWING " + _carrierName;

  m_msgs << "State           : " << stateStr       << "\n";
  m_msgs << "Pickup range    : " << (2.0 * _minChaseDist) << " m (3-D)\n";
  m_msgs << "Boundary radius : " << _boundaryRadius << " m from origin\n";
  m_msgs << "Dist from origin: "
         << std::sqrt(_navX * _navX + _navY * _navY) << " m\n";
  return true;
}
