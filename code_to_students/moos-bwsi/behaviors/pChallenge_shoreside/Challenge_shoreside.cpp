/************************************************************/
/*    FILE: Challenge_shoreside.cpp                         */
/*    ORGN: BWSI AUVC                                       */
/************************************************************/
#include "Challenge_shoreside.h"
#include "MBUtils.h"
#include <algorithm>
#include <sstream>

using namespace std;

Challenge_shoreside::Challenge_shoreside()
  : _whaleScore(300),
    _fishScore(100),
    _pickupScore(200),
    _collectScore(500),
    _biteTimeout(60),
    _gameLengthMin(20),
    _startTime(std::numeric_limits<double>::max())
{}

bool Challenge_shoreside::OnNewMail(MOOSMSG_LIST& NewMail) {
  AppCastingMOOSApp::OnNewMail(NewMail);

  for (CMOOSMsg& msg : NewMail) {
    const string& key = msg.GetKey();

    if (key == "WHALE_TAGGED")       _whaleTags.push(msg.GetString());
    else if (key == "FISH_PHOTOED")       _fishPhotos.push(msg.GetString());
    else if (key == "TREASURE_FOUND")     _treasuresFound.push(msg.GetString());
    else if (key == "TREASURE_RECOVERED") _treasuresRecovered.push(msg.GetString());
    else if (key == "SHARK_BITE")         _sharkBites.push(msg.GetString());
    else if (key == "NODE_REPORT") {
      // Register any new team encountered in a node report
      NodeReport r = NodeReport::fromString(msg.GetString());
      if (r.valid() && !r.group().empty() && r.group() != "npc")
        _teamScore.emplace(r.group(), 0);
    }
    else if (key == "DEPLOY_ALL") {
      const double now = MOOSTime();
      if (msg.GetString() == "true" && _startTime > now)
        _startTime = now;
    }
  }
  return true;
}

bool Challenge_shoreside::OnConnectToServer() {
  RegisterVariables();
  return true;
}

bool Challenge_shoreside::Iterate() {
  AppCastingMOOSApp::Iterate();

  const double now = MOOSTime();

  // End game when time is up
  if ((now - _startTime) > static_cast<double>(_gameLengthMin * 60)) {
    Notify("DEPLOY_ALL", "false");
    AppCastingMOOSApp::PostReport();
    return true;
  }

  // Process whale tags
  while (!_whaleTags.empty()) {
    NodeReport r = NodeReport::fromString(_whaleTags.front());
    _whaleTags.pop();
    if (!r.valid()) continue;
    _teamScore[r.group()] += _whaleScore;
    m_msgs << r.name() << " (" << r.type() << ") tagged "
           << r.getString("WHALE") << " for team " << r.group() << "\n";
  }

  // Process fish photos
  while (!_fishPhotos.empty()) {
    NodeReport r = NodeReport::fromString(_fishPhotos.front());
    _fishPhotos.pop();
    if (!r.valid()) continue;
    _teamScore[r.group()] += _fishScore;
    m_msgs << r.name() << " (" << r.type() << ") photographed "
           << r.getString("FISH") << " for team " << r.group() << "\n";
  }

  // Process treasure pickups
  while (!_treasuresFound.empty()) {
    NodeReport r = NodeReport::fromString(_treasuresFound.front());
    _treasuresFound.pop();
    if (!r.valid()) continue;
    _teamScore[r.group()] += _pickupScore;
    m_msgs << r.name() << " (" << r.type() << ") picked up "
           << r.getString("TREASURE") << " for team " << r.group() << "\n";
  }

  // Process treasure deliveries
  while (!_treasuresRecovered.empty()) {
    NodeReport r = NodeReport::fromString(_treasuresRecovered.front());
    _treasuresRecovered.pop();
    if (!r.valid()) continue;
    _teamScore[r.group()] += _collectScore;
    m_msgs << r.name() << " (" << r.type() << ") delivered "
           << r.getString("TREASURE") << " for team " << r.group() << "\n";
  }

  // Process shark bites — put victim in penalty box
  while (!_sharkBites.empty()) {
    NodeReport r = NodeReport::fromString(_sharkBites.front());
    _sharkBites.pop();
    if (!r.valid()) continue;

    m_msgs << r.name() << " (" << r.type() << ") was bitten by "
           << r.getString("SHARK") << " — penalty box for "
           << _biteTimeout << " s\n";

    string vname = r.name();
    for (char& c : vname) c = static_cast<char>(toupper(c));

    Notify("DEPLOY_" + vname,                 "false");
    Notify("MOOS_MANUAL_OVERRIDE_" + vname,   "true");
    _timeoutQueue.push({vname, now + static_cast<double>(_biteTimeout)});
  }

  // Release vehicles whose penalty time has expired
  while (!_timeoutQueue.empty() && now >= _timeoutQueue.front().second) {
    const string& vname = _timeoutQueue.front().first;
    Notify("MOOS_MANUAL_OVERRIDE_" + vname, "false");
    Notify("DEPLOY_" + vname,               "true");
    _timeoutQueue.pop();
  }

  AppCastingMOOSApp::PostReport();
  return true;
}

bool Challenge_shoreside::OnStartUp() {
  AppCastingMOOSApp::OnStartUp();

  list<string> sParams;
  m_MissionReader.EnableVerbatimQuoting(false);
  if (m_MissionReader.GetConfiguration(GetAppName(), sParams)) {
    for (string& line : sParams) {
      string param = tolower(biteStringX(line, '='));
      string value = line;
      if      (param == "whale_score")   _whaleScore   = stoi(value);
      else if (param == "fish_score")    _fishScore    = stoi(value);
      else if (param == "pickup_score")  _pickupScore  = stoi(value);
      else if (param == "collect_score") _collectScore = stoi(value);
      else if (param == "bite_timeout")  _biteTimeout  = stoi(value);
      else if (param == "game_length")   _gameLengthMin= stoi(value);
    }
  }

  RegisterVariables();
  return true;
}

void Challenge_shoreside::RegisterVariables() {
  AppCastingMOOSApp::RegisterVariables();
  Register("WHALE_TAGGED",        0);
  Register("FISH_PHOTOED",        0);
  Register("TREASURE_FOUND",      0);
  Register("TREASURE_RECOVERED",  0);
  Register("SHARK_BITE",          0);
  Register("NODE_REPORT",         0);
  Register("DEPLOY_ALL",          0);
}

bool Challenge_shoreside::buildReport() {
  const double now = MOOSTime();
  const double elapsed = (now < _startTime) ? 0.0 : (now - _startTime);
  const double remaining = static_cast<double>(_gameLengthMin * 60) - elapsed;

  m_msgs << "=== GAME STATUS ===\n";
  if (_startTime > now)
    m_msgs << "Game not started (waiting for DEPLOY_ALL=true)\n\n";
  else
    m_msgs << "Elapsed : " << static_cast<int>(elapsed)   << " s  |  "
           << "Remaining: " << static_cast<int>(remaining) << " s\n\n";

  m_msgs << "=== SCORES ===\n";
  for (const auto& kv : _teamScore)
    m_msgs << "  " << kv.first << " : " << kv.second << "\n";

  m_msgs << "\n=== PENALTY BOX ===\n";
  if (_timeoutQueue.empty()) {
    m_msgs << "  (empty)\n";
  }
  else {
    // We only peek at the front since the queue doesn't support iteration
    m_msgs << "  " << _timeoutQueue.size() << " vehicle(s) serving timeout\n";
  }
  return true;
}
