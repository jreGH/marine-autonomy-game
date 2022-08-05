/************************************************************/
/*    NAME:                                               */
/*    ORGN: MIT                                             */
/*    FILE: Challenge_shoreside.cpp                                        */
/*    DATE:                                                 */
/************************************************************/

#include <iterator>
#include "MBUtils.h"
#include "Challenge_shoreside.h"

using namespace std;

//-----------------------------------------
// Utility functions
std::map<std::string, std::string> ReadNodeReport(std::string report) {
  std::map<std::string, std::string> thisMap;

  std::string key, val;
  std::istringstream iss(report);

  while (std::getline(std::getline(iss, key, '=') >> std::ws, val, ','))
    thisMap[key] = val;

  return thisMap;

}

bool SameContact(std::map<std::string, std::string> A, std::map<std::string, std::string> B) {
  return ( (A["NAME"].compare(B["NAME"])==0) && (A["TYPE"].compare(B["TYPE"])==0));
}

//---------------------------------------------------------
// Constructor

Challenge_shoreside::Challenge_shoreside()
{
  _startTime = std::numeric_limits<double>::max();
  _gameLengthMin = 20;
}

//---------------------------------------------------------
// Destructor

Challenge_shoreside::~Challenge_shoreside()
{
}

//---------------------------------------------------------
// Procedure: OnNewMail

bool Challenge_shoreside::OnNewMail(MOOSMSG_LIST &NewMail)
{

  std::cout << "On new mail.." << std::endl;
  AppCastingMOOSApp::OnNewMail(NewMail);

  MOOSMSG_LIST::iterator p;
   
  for(p=NewMail.begin(); p!=NewMail.end(); p++) {
    CMOOSMsg &msg = *p;

    std::string key = msg.GetKey();

    if (key.compare("WHALE_TAGGED") == 0) {
      _whaleTags.push(msg.GetString());
    }
    else if (key.compare("FISH_PHOTOED") == 0) {
      _fishPhotos.push(msg.GetString());
    }
    else if (key.compare("TREASURE_FOUND") == 0) {
      _treasuresFound.push(msg.GetString());
    }
    else if (key.compare("TREASURE_RECOVERED") == 0) {
      _treasuresRecovered.push(msg.GetString());
    }
    else if (key.compare("SHARK_BITE") == 0) {
      _timeouts.push(msg.GetString());
    }
    else if (key.compare("NODE_REPORT") == 0) {
      _nodeReports.push(msg.GetString());
    }
    else if (key.compare("DEPLOY_ALL") == 0) {
      double time_now = MOOSTime();
      if ((msg.GetString().compare("true")==0) && (_startTime > time_now)) {
        _startTime = MOOSTime();
      }
    }

#if 0 // Keep these around just for template
    string key   = msg.GetKey();
    string comm  = msg.GetCommunity();
    double dval  = msg.GetDouble();
    string sval  = msg.GetString(); 
    string msrc  = msg.GetSource();
    double mtime = msg.GetTime();
    bool   mdbl  = msg.IsDouble();
    bool   mstr  = msg.IsString();
#endif
  
  }

  return(true);
}

//---------------------------------------------------------
// Procedure: OnConnectToServer

bool Challenge_shoreside::OnConnectToServer()
{
   RegisterVariables();
   return(true);
}

//---------------------------------------------------------
// Procedure: Iterate()
//            happens AppTick times per second

bool Challenge_shoreside::Iterate()
{
  AppCastingMOOSApp::Iterate();

  // is the game over?
  double time_now = MOOSTime();
  if ( (time_now-_startTime) > (double)(_gameLengthMin*60) ) {
    Notify("DEPLOY_ALL", "false");
    return(true);
  }

  // deal with all of the node reports
  while (!_nodeReports.empty()){
    std::string report = _nodeReports.front();
 
    // convert the report into a "dictionary"
    std::map<std::string, std::string> thisContact = ReadNodeReport(report);

    if (_teamScore.count(thisContact["GROUP"]) == 0) {
      _teamScore.insert({thisContact["GROUP"], 0});
    }

    _nodeReports.pop();
  }

  // did somebody tag a whale??
  while (!_whaleTags.empty()) {
    std::string tag = _whaleTags.front();

    // parse the message
    std::map<std::string, std::string> thisTag = ReadNodeReport(tag);
    m_msgs << thisTag["SRC"] << "(" << thisTag["TYPE"] << ") has tagged a " << thisTag["WHALE"] << " for team " << thisTag["GROUP"] << "!" << std::endl;
    _teamScore[thisTag["GROUP"]] += _whaleScore;

    _whaleTags.pop();
  }

  // did somebody photo a fish??
  while (!_fishPhotos.empty()) {
    std::string tag = _fishPhotos.front();

    // parse the message
    std::map<std::string, std::string> thisTag = ReadNodeReport(tag);
    m_msgs << thisTag["SRC"] << "(" << thisTag["TYPE"] << ") has photographed a " << thisTag["FISH"] << " for team " << thisTag["GROUP"] << "!" << std::endl;
    _teamScore[thisTag["GROUP"]] += _fishScore;

    _fishPhotos.pop();
  }

  // did somebody pick up a treasure?
  while (!_treasuresFound.empty()) {
    std::string treas = _treasuresFound.front();

    // parse the message
    std::map<std::string, std::string> thisTreas = ReadNodeReport(treas);
    m_msgs << thisTreas["SRC"] << "(" << thisTreas["TYPE"] << ") has picked up a " << thisTreas["TREASURE"] << " for team " << thisTreas["GROUP"] << "!" << std::endl;  
    _teamScore[thisTreas["GROUP"]] += _pickupScore;

    _treasuresFound.pop();
  }

  // did somebody pick up a treasure?
  while (!_treasuresRecovered.empty()) {
    std::string treas = _treasuresRecovered.front();

    // parse the message
    std::map<std::string, std::string> thisTreas = ReadNodeReport(treas);
    m_msgs << thisTreas["SRC"] << "(" << thisTreas["TYPE"] << ") has collected the " << thisTreas["TREASURE"] << " treasure for team " << thisTreas["GROUP"] << "!" << std::endl;  
    _teamScore[thisTreas["GROUP"]] += _collectScore;

    _treasuresRecovered.pop();
  }

  double now = MOOSTime();
  while (!_timeouts.empty()) {
    std::string attack = _timeouts.front();
    std::map<std::string, std::string> thisBite = ReadNodeReport(attack);
    m_msgs << thisBite["SRC"] << "(" << thisBite["TYPE"] << ") was bitten by " << thisBite["SHARK"] << std::endl;

    if (_teamScore.count("npc") > 0) {
      _teamScore["npc"] += 100;
    }

    std::string uxv = thisBite["SRC"];
    for (auto & c : uxv) c = toupper(c); // Why is toupper such a pain in C++?
    std::string varname = "DEPLOY_" + uxv;
    Notify(varname, "false");
    varname = "MOOS_MANUAL_OVERRIDE_" + uxv;
    Notify(varname, "true");
    _timeoutList.push({uxv, now + _biteTimeout});
    _timeouts.pop();
  }

  // free anyone ready to leave the penalty box
  bool done = false;
  while (!done && !_timeoutList.empty()) {
    std::pair<std::string, double> timeout = _timeoutList.front();
    if (now > timeout.second) {
      std::string varname = "MOOS_MANUAL_OVERRIDE_" + timeout.first;
      Notify(varname, "false");
      
      varname = "DEPLOY_" + timeout.first;
      Notify(varname, "true");
      _timeoutList.pop();
    }
    else {
      done = true;
    }
  }

  AppCastingMOOSApp::PostReport();

  return(true);
}

//---------------------------------------------------------
// Procedure: OnStartUp()
//            happens before connection is open

bool Challenge_shoreside::OnStartUp()
{

  AppCastingMOOSApp::OnStartUp();

  list<string> sParams;
  m_MissionReader.EnableVerbatimQuoting(false);
  if(m_MissionReader.GetConfiguration(GetAppName(), sParams)) {
    list<string>::iterator p;
    for(p=sParams.begin(); p!=sParams.end(); p++) {
      string line  = *p;
      string param = tolower(biteStringX(line, '='));
      string value = line;
      
      if(param == "whale_score") {
        _whaleScore = std::stoi(value);
      }
      else if(param == "fish_score") {
        _fishScore = std::stoi(value);
      }
      else if(param == "pickup_score") {
        _pickupScore = std::stoi(value);
      }
      else if(param == "collect_score") {
        _collectScore = std::stoi(value);
      }
      else if(param == "bite_timeout") {
        _biteTimeout = std::stoi(value);
      }
      else if(param == "game_length") {
        _gameLengthMin = std::stoi(value);
      }
    }
  }
  
  RegisterVariables();	
  return(true);
}

//---------------------------------------------------------
// Procedure: RegisterVariables

void Challenge_shoreside::RegisterVariables()
{

  AppCastingMOOSApp::RegisterVariables();

  std::cout << "Registering variables..." << std::endl;
  Register("WHALE_TAGGED", 0);
  Register("FISH_PHOTOED", 0);
  Register("TREASURE_FOUND", 0);
  Register("TREASURE_RECOVERED", 0);
  Register("SHARK_BITE", 0);
  Register("NODE_REPORT", 0);
  Register("DEPLOY_ALL", 0);
}

bool Challenge_shoreside::buildReport()
{
  m_msgs << "***********CURRENT SCORE***************" << std::endl;
  for (auto const &teamscore : _teamScore) {
    m_msgs << teamscore.first << ": " << teamscore.second << std::endl;
  }

  return(true);
}
