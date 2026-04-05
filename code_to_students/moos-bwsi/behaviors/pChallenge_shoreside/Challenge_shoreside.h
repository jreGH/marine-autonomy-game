/************************************************************/
/*    FILE: Challenge_shoreside.h                           */
/*    ORGN: BWSI AUVC                                       */
/*                                                          */
/*    Referee / scorekeeper running on the shoreside MOOS   */
/*    community.  Tracks team scores, applies shark-bite    */
/*    timeouts, and ends the game after game_length_min.    */
/*                                                          */
/*    Config params (all optional, defaults shown):         */
/*      whale_score    = 300                                */
/*      fish_score     = 100                                */
/*      pickup_score   = 200                                */
/*      collect_score  = 500                                */
/*      bite_timeout   = 60    // penalty box duration (s) */
/*      game_length    = 20    // total game duration (min) */
/*                                                          */
/*    Subscribes:                                           */
/*      WHALE_TAGGED        NODE_REPORT    DEPLOY_ALL       */
/*      FISH_PHOTOED        SHARK_BITE                      */
/*      TREASURE_FOUND      TREASURE_RECOVERED              */
/*                                                          */
/*    Publishes:                                            */
/*      DEPLOY_ALL              = true/false                */
/*      DEPLOY_<VEHICLE>        = false  (on bite)          */
/*      MOOS_MANUAL_OVERRIDE_<V>= true/false (timeout)     */
/************************************************************/
#pragma once

#include "MOOS/libMOOS/MOOSLib.h"
#include "MOOS/libMOOS/Thirdparty/AppCasting/AppCastingMOOSApp.h"
#include "NodeReport.h"
#include <map>
#include <queue>
#include <string>
#include <utility>

class Challenge_shoreside : public AppCastingMOOSApp {
public:
  Challenge_shoreside();
  ~Challenge_shoreside() {}

protected:
  bool OnNewMail(MOOSMSG_LIST& NewMail);
  bool Iterate();
  bool OnConnectToServer();
  bool OnStartUp();
  bool buildReport();

  void RegisterVariables();

private:
  // Configuration (all have defaults)
  int    _whaleScore;     // points for tagging a whale
  int    _fishScore;      // points for photographing a fish
  int    _pickupScore;    // points for picking up treasure
  int    _collectScore;   // points for delivering treasure to base
  int    _biteTimeout;    // seconds a bitten vehicle sits in the penalty box
  int    _gameLengthMin;  // total game duration in minutes

  // Runtime state
  double _startTime;                         // MOOSTime() when DEPLOY_ALL=true received
  std::map<std::string, int> _teamScore;     // group → score

  // Event queues (raw strings from MOOSDB)
  std::queue<std::string> _whaleTags;
  std::queue<std::string> _fishPhotos;
  std::queue<std::string> _treasuresFound;
  std::queue<std::string> _treasuresRecovered;
  std::queue<std::string> _sharkBites;

  // Penalty-box queue: (VEHICLE_NAME_UPPER, release_time)
  std::queue<std::pair<std::string, double>> _timeoutQueue;
};
