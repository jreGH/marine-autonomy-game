/************************************************************/
/*    FILE: Challenge_fish.h                                */
/*    ORGN: BWSI AUVC                                       */
/*                                                          */
/*    NPC fish: patrols and flees from approaching player   */
/*    vehicles.  When a player comes within photo range     */
/*    (2 * min_chase_dist in 3-D) the fish is considered    */
/*    photographed: FISH_PHOTOED is published and fleeing   */
/*    stops.                                                */
/*                                                          */
/*    Config params (all optional, defaults shown):         */
/*      name           = fish                               */
/*      min_chase_dist = 5.0   // photo range = 2x this (m) */
/*      max_chase_dist = 40.0  // flee trigger range (m)    */
/*                                                          */
/*    Publishes:                                             */
/*      ESCAPE        = true/false                          */
/*      PATROL        = true/false                          */
/*      AVOID_UPDATES = "contact=<name>"                    */
/*      FISH_PHOTOED  = "SRC=...,TYPE=...,GROUP=...,FISH=..."*/
/*      TAGGED        = true                                */
/************************************************************/
#pragma once

#include "MOOS/libMOOS/MOOSLib.h"
#include "MOOS/libMOOS/Thirdparty/AppCasting/AppCastingMOOSApp.h"
#include "ContactTracker.h"
#include <string>

class Challenge_fish : public AppCastingMOOSApp {
public:
  Challenge_fish();
  ~Challenge_fish() {}

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
  double _minChaseDist; // photo range = 2 * this (3-D)
  double _maxChaseDist; // flee trigger range (2-D)

  // Own-vehicle navigation state
  double _navX;
  double _navY;
  double _navDepth;

  // Contact management
  ContactTracker _tracker;

  bool _isTagged;
};
