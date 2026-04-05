/************************************************************/
/*    FILE: Challenge_whale.h                               */
/*    ORGN: BWSI AUVC                                       */
/*                                                          */
/*    NPC whale: patrols and flees from surface vehicles    */
/*    (contacts with depth < surface_depth_threshold).      */
/*    Tagged when a surface vehicle comes within            */
/*    min_chase_dist.  Deep vehicles (AUVs) are ignored.   */
/*                                                          */
/*    Config params (all optional, defaults shown):         */
/*      name                   = whale                      */
/*      min_chase_dist         = 5.0   // tag range (m)    */
/*      max_chase_dist         = 40.0  // flee range (m)   */
/*      surface_depth_threshold = 5.0  // depth < this → surface vehicle */
/*                                                          */
/*    Publishes:                                             */
/*      ESCAPE     = true/false                             */
/*      PATROL     = true/false                             */
/*      AVOID_UPDATES = "contact=<name>"                    */
/*      WHALE_TAGGED  = "SRC=...,TYPE=...,GROUP=...,WHALE=..."*/
/*      TAGGED_BY  = <vehicle name>                         */
/*      TAGGED     = true                                   */
/************************************************************/
#pragma once

#include "MOOS/libMOOS/MOOSLib.h"
#include "MOOS/libMOOS/Thirdparty/AppCasting/AppCastingMOOSApp.h"
#include "ContactTracker.h"
#include <string>

class Challenge_whale : public AppCastingMOOSApp {
public:
  Challenge_whale();
  ~Challenge_whale() {}

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
  double _minChaseDist;          // tag range (m)
  double _maxChaseDist;          // flee trigger range (m)
  double _surfaceDepthThreshold; // contacts shallower than this are "surface"

  // Own-vehicle navigation state
  double _navX;
  double _navY;
  double _navDepth;

  // Contact management
  ContactTracker _tracker;

  bool _isTagged;
};
