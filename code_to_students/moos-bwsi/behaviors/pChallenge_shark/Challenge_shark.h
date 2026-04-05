/************************************************************/
/*    FILE: Challenge_shark.h                               */
/*    ORGN: BWSI AUVC                                       */
/*                                                          */
/*    NPC shark: patrols, detects player vehicles by        */
/*    NODE_REPORT, chases them in 3-D, and "bites" when     */
/*    within min range.  A bitten vehicle is reported to    */
/*    pChallenge_shoreside via SHARK_BITE and placed in a   */
/*    penalty timeout by the shoreside.                     */
/*                                                          */
/*    Config params (all optional, defaults shown):         */
/*      name              = shark          // this shark's name   */
/*      min_chase_dist    = 5.0   // bite range (m, 3-D)          */
/*      max_chase_dist    = 50.0  // detection range (m, 2-D)     */
/*      chase_timeout     = 30.0  // give up chase after N sec    */
/*      recovery_timeout  = 120.0 // cooldown before next chase   */
/*                                                          */
/*    Publishes:                                             */
/*      CHASE                 = true/false                  */
/*      PATROL                = true/false                  */
/*      CHASE_UPDATES         = "contact=<name>"            */
/*      CONSTANT_DEPTH_UPDATES= <depth>                     */
/*      SHARK_BITE            = "SRC=...,TYPE=...,GROUP=...,SHARK=..."  */
/************************************************************/
#pragma once

#include "MOOS/libMOOS/MOOSLib.h"
#include "MOOS/libMOOS/Thirdparty/AppCasting/AppCastingMOOSApp.h"
#include "ContactTracker.h"
#include <limits>
#include <string>

class Challenge_shark : public AppCastingMOOSApp {
public:
  Challenge_shark();
  ~Challenge_shark() {}

protected:
  bool OnNewMail(MOOSMSG_LIST& NewMail);
  bool Iterate();
  bool OnConnectToServer();
  bool OnStartUp();
  bool buildReport();

  void RegisterVariables();

private:
  // Configuration
  std::string _myName;
  double _minChaseDist;    // 3-D bite range (m)
  double _maxChaseDist;    // 2-D detection range (m)
  double _chaseTimeout;    // seconds before giving up a chase
  double _recoveryTimeout; // seconds of cooldown after a chase

  // Own-vehicle navigation state
  double _navX;
  double _navY;
  double _navDepth;

  // Contact management
  ContactTracker _tracker;

  // Chase state machine
  enum State { PATROLLING, CHASING, RECOVERING };
  State  _state;
  double _chaseStartTime;
  double _recoveryStartTime;
  std::string _chaseTarget; // name of vehicle currently being chased
};
