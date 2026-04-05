/************************************************************/
/*    FILE: Challenge_fish.cpp                              */
/*    ORGN: BWSI AUVC                                       */
/************************************************************/
#include "Challenge_fish.h"
#include "MBUtils.h"
#include <sstream>

using namespace std;

Challenge_fish::Challenge_fish()
  : _myName("fish"),
    _minChaseDist(5.0),
    _maxChaseDist(40.0),
    _navX(0), _navY(0), _navDepth(0),
    _isTagged(false)
{}

bool Challenge_fish::OnNewMail(MOOSMSG_LIST& NewMail) {
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

bool Challenge_fish::OnConnectToServer() {
  RegisterVariables();
  return true;
}

bool Challenge_fish::Iterate() {
  AppCastingMOOSApp::Iterate();

  // If no contacts for many iterations, return to patrol
  if (_tracker.emptyCount() > 25) {
    Notify("ESCAPE", "false");
    Notify("PATROL", "true");
  }

  if (_isTagged) {
    AppCastingMOOSApp::PostReport();
    return true;
  }

  const double photoRange = 2.0 * _minChaseDist;

  for (const NodeReport& contact : _tracker.contacts()) {
    const double dist2D  = contact.distanceTo2D(_navX, _navY);
    const double range3D = contact.rangeTo3D(_navX, _navY, _navDepth);

    if (range3D < photoRange) {
      // Photographed!
      ostringstream evt;
      evt << "SRC="   << contact.name()
          << ",TYPE=" << contact.type()
          << ",GROUP="<< contact.group()
          << ",FISH=" << _myName;
      Notify("FISH_PHOTOED", evt.str());
      Notify("TAGGED", "true");
      Notify("ESCAPE", "false");
      _tracker.markCollected(contact);
      _isTagged = true;
      break;
    }
    else if (dist2D < _maxChaseDist) {
      // Flee from approaching contact
      Notify("AVOID_UPDATES", "contact=" + contact.name());
      Notify("ESCAPE", "true");
      Notify("PATROL", "false");
    }
    else {
      // Contact moved out of range — resume patrol
      Notify("ESCAPE", "false");
      Notify("PATROL", "true");
    }
  }

  AppCastingMOOSApp::PostReport();
  return true;
}

bool Challenge_fish::OnStartUp() {
  AppCastingMOOSApp::OnStartUp();

  list<string> sParams;
  m_MissionReader.EnableVerbatimQuoting(false);
  if (m_MissionReader.GetConfiguration(GetAppName(), sParams)) {
    for (string& line : sParams) {
      string param = tolower(biteStringX(line, '='));
      string value = line;
      if      (param == "name")           _myName       = value;
      else if (param == "min_chase_dist") _minChaseDist = stod(value);
      else if (param == "max_chase_dist") _maxChaseDist = stod(value);
    }
  }

  RegisterVariables();
  return true;
}

void Challenge_fish::RegisterVariables() {
  AppCastingMOOSApp::RegisterVariables();
  Register("NAV_X",             0);
  Register("NAV_Y",             0);
  Register("NAV_DEPTH",         0);
  Register("NODE_REPORT",       0);
  Register("NODE_REPORT_LOCAL", 0);
}

bool Challenge_fish::buildReport() {
  m_msgs << "State       : " << (_isTagged ? "TAGGED" : "ACTIVE") << "\n";
  m_msgs << "Photo range : " << (2.0 * _minChaseDist) << " m (3-D)\n";
  m_msgs << "Flee range  : " << _maxChaseDist         << " m (2-D)\n";
  m_msgs << "Contacts    : " << _tracker.contacts().size() << "\n";
  m_msgs << "Empty iters : " << _tracker.emptyCount() << "\n";
  return true;
}
