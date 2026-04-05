/************************************************************/
/*    FILE: Challenge.h                                     */
/*    ORGN: BWSI AUVC                                       */
/*                                                          */
/*    Student vehicle logic.  This process reads its own    */
/*    navigation state and NODE_REPORTs from other vehicles */
/*    and decides whether to chase a contact or loiter.     */
/*                                                          */
/*    Config params (all optional, defaults shown):         */
/*      min_chase_dist = 5.0   // "caught" range (m, 2-D)  */
/*      max_chase_dist = 50.0  // detection range (m, 2-D) */
/*                                                          */
/*    Publishes:                                            */
/*      CLOSE         = true/false                          */
/*      LOITER        = true/false                          */
/*      CHASE_UPDATES = "contact=<name>"                    */
/************************************************************/
#pragma once

#include "MOOS/libMOOS/MOOSLib.h"
#include "ContactTracker.h"
#include <string>

class Challenge : public CMOOSApp {
public:
  Challenge();
  ~Challenge() {}

protected:
  bool OnNewMail(MOOSMSG_LIST& NewMail);
  bool Iterate();
  bool OnConnectToServer();
  bool OnStartUp();

  void RegisterVariables();

private:
  // Configuration
  double _minChaseDist;
  double _maxChaseDist;

  // Own-vehicle navigation state
  double _navX;
  double _navY;
  double _navDepth;

  // Contact management
  ContactTracker _tracker;
};
