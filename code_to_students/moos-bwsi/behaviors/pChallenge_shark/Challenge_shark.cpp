/************************************************************/
/*    FILE: Challenge_shark.cpp                             */
/*    ORGN: BWSI AUVC                                       */
/************************************************************/
#include "Challenge_shark.h"
#include "MBUtils.h"
#include <sstream>

using namespace std;

Challenge_shark::Challenge_shark()
  : _myName("shark"),
    _minChaseDist(5.0),
    _maxChaseDist(50.0),
    _chaseTimeout(30.0),
    _recoveryTimeout(120.0),
    _navX(0), _navY(0), _navDepth(0),
    _state(PATROLLING),
    _chaseStartTime(0),
    _recoveryStartTime(0)
{}

bool Challenge_shark::OnNewMail(MOOSMSG_LIST& NewMail) {
  AppCastingMOOSApp::OnNewMail(NewMail);

  bool gotReport = false;
  for (CMOOSMsg& msg : NewMail) {
    const string& key = msg.GetKey();
    if      (key == "NAV_X")           _navX     = msg.GetDouble();
    else if (key == "NAV_Y")           _navY     = msg.GetDouble();
    else if (key == "NAV_DEPTH")       _navDepth = msg.GetDouble();
    else if (key == "NODE_REPORT" || key == "NODE_REPORT_LOCAL") {
      _tracker.processReport(msg.GetString());
      gotReport = true;
    }
  }

  if (gotReport)
    _tracker.tickReceived();
  else
    _tracker.tickEmpty();

  return true;
}

bool Challenge_shark::OnConnectToServer() {
  RegisterVariables();
  return true;
}

bool Challenge_shark::Iterate() {
  AppCastingMOOSApp::Iterate();

  const double now = MOOSTime();

  // State transitions triggered by timers
  if (_state == CHASING && (now - _chaseStartTime) > _chaseTimeout) {
    _state = RECOVERING;
    _recoveryStartTime = now;
    _chaseTarget = "";
    Notify("CHASE", "false");
    Notify("PATROL", "true");
    Notify("CHASE_UPDATES", "contact=NOBODY");
    Notify("CONSTANT_DEPTH_UPDATES", 20.0);
  }
  if (_state == RECOVERING && (now - _recoveryStartTime) > _recoveryTimeout) {
    _state = PATROLLING;
  }

  // If we've had no contacts for many iterations, ensure we are patrolling
  if (_tracker.emptyCount() > 25 && _state == CHASING) {
    _state = PATROLLING;
    _chaseTarget = "";
    Notify("CHASE", "false");
    Notify("PATROL", "true");
    Notify("CHASE_UPDATES", "contact=NOBODY");
    Notify("CONSTANT_DEPTH_UPDATES", 20.0);
  }

  // Evaluate contacts
  for (const NodeReport& contact : _tracker.contacts()) {
    // NPCs don't bite each other
    if (contact.group() == "npc")
      continue;
    // Don't re-engage a vehicle we already bit this chase cycle
    if (_tracker.isCollected(contact))
      continue;
    // Don't chase while recovering
    if (_state == RECOVERING)
      continue;

    const double dist2D  = contact.distanceTo2D(_navX, _navY);
    const double range3D = contact.rangeTo3D(_navX, _navY, _navDepth);

    if (range3D < _minChaseDist) {
      // Bite!
      ostringstream bite;
      bite << "SRC="   << contact.name()
           << ",TYPE=" << contact.type()
           << ",GROUP="<< contact.group()
           << ",SHARK=" << _myName;
      Notify("SHARK_BITE", bite.str());
      _tracker.markCollected(contact);

      _state = PATROLLING;
      _chaseTarget = "";
      Notify("CHASE", "false");
      Notify("PATROL", "true");
      Notify("CHASE_UPDATES", "contact=NOBODY");
      Notify("CONSTANT_DEPTH_UPDATES", 20.0);
    }
    else if (dist2D > _maxChaseDist) {
      if (_state == CHASING && _chaseTarget == contact.name()) {
        _state = PATROLLING;
        _chaseTarget = "";
        Notify("CHASE", "false");
        Notify("PATROL", "true");
        Notify("CHASE_UPDATES", "contact=NOBODY");
        Notify("CONSTANT_DEPTH_UPDATES", 20.0);
      }
    }
    else if (_state == PATROLLING && dist2D < _maxChaseDist) {
      // Start chase
      _state = CHASING;
      _chaseTarget = contact.name();
      _chaseStartTime = now;
      Notify("CHASE_UPDATES", "contact=" + contact.name());
      Notify("CHASE", "true");
      Notify("PATROL", "false");
      Notify("CONSTANT_DEPTH_UPDATES", contact.depth());
    }
  }

  AppCastingMOOSApp::PostReport();
  return true;
}

bool Challenge_shark::OnStartUp() {
  AppCastingMOOSApp::OnStartUp();

  list<string> sParams;
  m_MissionReader.EnableVerbatimQuoting(false);
  if (m_MissionReader.GetConfiguration(GetAppName(), sParams)) {
    for (string& line : sParams) {
      string param = tolower(biteStringX(line, '='));
      string value = line;
      if      (param == "name")             _myName          = value;
      else if (param == "min_chase_dist")   _minChaseDist    = stod(value);
      else if (param == "max_chase_dist")   _maxChaseDist    = stod(value);
      else if (param == "chase_timeout")    _chaseTimeout    = stod(value);
      else if (param == "recovery_timeout") _recoveryTimeout = stod(value);
    }
  }

  RegisterVariables();
  return true;
}

void Challenge_shark::RegisterVariables() {
  AppCastingMOOSApp::RegisterVariables();
  Register("NAV_X",             0);
  Register("NAV_Y",             0);
  Register("NAV_DEPTH",         0);
  Register("NODE_REPORT",       0);
  Register("NODE_REPORT_LOCAL", 0);
}

bool Challenge_shark::buildReport() {
  string stateStr;
  switch (_state) {
    case PATROLLING: stateStr = "PATROLLING"; break;
    case CHASING:    stateStr = "CHASING";    break;
    case RECOVERING: stateStr = "RECOVERING"; break;
  }
  m_msgs << "State       : " << stateStr << "\n";
  if (_state == CHASING)
    m_msgs << "Target      : " << _chaseTarget << "\n"
           << "Chase time  : " << (MOOSTime() - _chaseStartTime) << " / "
           << _chaseTimeout << " s\n";
  if (_state == RECOVERING)
    m_msgs << "Recovery    : " << (MOOSTime() - _recoveryStartTime) << " / "
           << _recoveryTimeout << " s\n";
  m_msgs << "Contacts    : " << _tracker.contacts().size() << "\n";
  m_msgs << "Empty iters : " << _tracker.emptyCount() << "\n";
  return true;
}
