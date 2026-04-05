/************************************************************/
/*    FILE: Challenge.cpp                                   */
/*    ORGN: BWSI AUVC                                       */
/*                                                          */
/*    Student vehicle logic.  When a contact is detected    */
/*    within max_chase_dist and has not yet been caught,    */
/*    it posts CLOSE=true and CHASE_UPDATES so the helm     */
/*    behaviour can pursue it.  Once within min_chase_dist  */
/*    the contact is marked collected.                      */
/************************************************************/
#include "Challenge.h"
#include "MBUtils.h"
#include <sstream>

using namespace std;

Challenge::Challenge()
  : _minChaseDist(5.0),
    _maxChaseDist(50.0),
    _navX(0), _navY(0), _navDepth(0)
{}

bool Challenge::OnNewMail(MOOSMSG_LIST& NewMail) {
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

bool Challenge::OnConnectToServer() {
  RegisterVariables();
  return true;
}

bool Challenge::Iterate() {
  for (const NodeReport& contact : _tracker.contacts()) {
    const double dist2D = contact.distanceTo2D(_navX, _navY);

    if (dist2D < _minChaseDist) {
      // Caught — mark so we don't re-chase this contact
      _tracker.markCollected(contact);
      Notify("CLOSE",  "false");
      Notify("LOITER", "true");
    }
    else if (dist2D > _maxChaseDist) {
      Notify("CLOSE",  "false");
      Notify("LOITER", "true");
    }
    else if (!_tracker.isCollected(contact)) {
      // In range and not yet caught — chase it
      Notify("CHASE_UPDATES", "contact=" + contact.name());
      Notify("CLOSE",  "true");
      Notify("LOITER", "false");
    }
  }
  return true;
}

bool Challenge::OnStartUp() {
  list<string> sParams;
  m_MissionReader.EnableVerbatimQuoting(false);
  if (m_MissionReader.GetConfiguration(GetAppName(), sParams)) {
    for (string& line : sParams) {
      string param = tolower(biteStringX(line, '='));
      string value = line;
      if      (param == "min_chase_dist") _minChaseDist = stod(value);
      else if (param == "max_chase_dist") _maxChaseDist = stod(value);
    }
  }

  RegisterVariables();
  return true;
}

void Challenge::RegisterVariables() {
  Register("NAV_X",             0);
  Register("NAV_Y",             0);
  Register("NAV_DEPTH",         0);
  Register("NODE_REPORT",       0);
  Register("NODE_REPORT_LOCAL", 0);
}
