/************************************************************/
/*    FILE: Challenge_whale.cpp                             */
/*    ORGN: BWSI AUVC                                       */
/************************************************************/
#include "Challenge_whale.h"
#include "MBUtils.h"
#include <sstream>

using namespace std;

Challenge_whale::Challenge_whale()
  : _myName("whale"),
    _minChaseDist(5.0),
    _maxChaseDist(40.0),
    _surfaceDepthThreshold(5.0),
    _navX(0), _navY(0), _navDepth(0),
    _isTagged(false)
{}

bool Challenge_whale::OnNewMail(MOOSMSG_LIST& NewMail) {
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

bool Challenge_whale::OnConnectToServer() {
  RegisterVariables();
  return true;
}

bool Challenge_whale::Iterate() {
  AppCastingMOOSApp::Iterate();

  if (_tracker.emptyCount() > 25) {
    Notify("ESCAPE", "false");
    Notify("PATROL", "true");
  }

  if (_isTagged) {
    AppCastingMOOSApp::PostReport();
    return true;
  }

  for (const NodeReport& contact : _tracker.contacts()) {
    // Only react to surface vehicles
    if (contact.depth() >= _surfaceDepthThreshold)
      continue;
    // NPCs don't interact with each other
    if (contact.group() == "npc")
      continue;

    const double dist2D = contact.distanceTo2D(_navX, _navY);

    if (dist2D < _minChaseDist) {
      // Tagged!
      ostringstream evt;
      evt << "SRC="    << contact.name()
          << ",TYPE="  << contact.type()
          << ",GROUP=" << contact.group()
          << ",WHALE=" << _myName;
      Notify("WHALE_TAGGED", evt.str());
      Notify("TAGGED_BY", contact.name());
      Notify("TAGGED", "true");
      Notify("ESCAPE", "false");
      _tracker.markCollected(contact);
      _isTagged = true;
      break;
    }
    else if (dist2D < _maxChaseDist) {
      // Flee
      Notify("AVOID_UPDATES", "contact=" + contact.name());
      Notify("ESCAPE", "true");
      Notify("PATROL", "false");
    }
    else {
      Notify("ESCAPE", "false");
      Notify("PATROL", "true");
    }
  }

  AppCastingMOOSApp::PostReport();
  return true;
}

bool Challenge_whale::OnStartUp() {
  AppCastingMOOSApp::OnStartUp();

  list<string> sParams;
  m_MissionReader.EnableVerbatimQuoting(false);
  if (m_MissionReader.GetConfiguration(GetAppName(), sParams)) {
    for (string& line : sParams) {
      string param = tolower(biteStringX(line, '='));
      string value = line;
      if      (param == "name")                    _myName                = value;
      else if (param == "min_chase_dist")           _minChaseDist          = stod(value);
      else if (param == "max_chase_dist")           _maxChaseDist          = stod(value);
      else if (param == "surface_depth_threshold")  _surfaceDepthThreshold = stod(value);
    }
  }

  RegisterVariables();
  return true;
}

void Challenge_whale::RegisterVariables() {
  AppCastingMOOSApp::RegisterVariables();
  Register("NAV_X",             0);
  Register("NAV_Y",             0);
  Register("NAV_DEPTH",         0);
  Register("NODE_REPORT",       0);
  Register("NODE_REPORT_LOCAL", 0);
}

bool Challenge_whale::buildReport() {
  m_msgs << "State             : " << (_isTagged ? "TAGGED" : "ACTIVE") << "\n";
  m_msgs << "Surface threshold : " << _surfaceDepthThreshold << " m\n";
  m_msgs << "Tag range         : " << _minChaseDist          << " m (2-D)\n";
  m_msgs << "Flee range        : " << _maxChaseDist           << " m (2-D)\n";
  m_msgs << "Contacts          : " << _tracker.contacts().size() << "\n";
  return true;
}
