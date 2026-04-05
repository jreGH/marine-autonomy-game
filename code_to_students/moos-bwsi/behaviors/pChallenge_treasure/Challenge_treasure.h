/************************************************************/
/*    FILE: Challenge_treasure.h                            */
/*    ORGN: BWSI AUVC                                       */
/*                                                          */
/*    NPC treasure: waits at its starting position until    */
/*    a player vehicle comes within pickup range.  Once     */
/*    picked up it follows the carrier (via BHV_Trail).     */
/*    When the carrier reaches the collection boundary it   */
/*    publishes TREASURE_RECOVERED and deactivates itself.  */
/*                                                          */
/*    Config params (all optional, defaults shown):         */
/*      name            = treasure                          */
/*      min_chase_dist  = 5.0    // pickup range (m, 3-D)  */
/*      boundary_radius = 1500.0 // distance from origin that */
/*                               // signals collection (m)  */
/*                                                          */
/*    Publishes:                                             */
/*      FOLLOW           = true/false                       */
/*      WAIT             = true/false                       */
/*      FOLLOW_UPDATES   = "contact=<name>"                 */
/*      STOLEN_BY        = "<name>,<type>,<group>"          */
/*      TREASURE_FOUND   = "SRC=...,TYPE=...,GROUP=...,TREASURE=..."*/
/*      TREASURE_RECOVERED = same format                    */
/*      DEPLOY           = false  (on collection)           */
/************************************************************/
#pragma once

#include "MOOS/libMOOS/MOOSLib.h"
#include "MOOS/libMOOS/Thirdparty/AppCasting/AppCastingMOOSApp.h"
#include "ContactTracker.h"
#include <string>

class Challenge_treasure : public AppCastingMOOSApp {
public:
  Challenge_treasure();
  ~Challenge_treasure() {}

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
  double _minChaseDist;    // pickup range (3-D, m)
  double _boundaryRadius;  // distance from origin that triggers collection

  // Own-vehicle navigation state
  double _navX;
  double _navY;
  double _navDepth;

  // Contact management
  ContactTracker _tracker;

  // State
  bool _isPickedUp;
  bool _isCollected;
  std::string _carrierName; // name of the vehicle currently carrying us
};
