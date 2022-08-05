/************************************************************/
/*    NAME:                                               */
/*    ORGN: MIT                                             */
/*    FILE: Challenge_whale.cpp                                        */
/*    DATE:                                                 */
/************************************************************/

#include <iterator>
#include "MBUtils.h"
#include "Challenge_whale.h"

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

Challenge_whale::Challenge_whale()
{
  _isTagged = false;
}

//---------------------------------------------------------
// Destructor

Challenge_whale::~Challenge_whale()
{
}

//---------------------------------------------------------
// Procedure: OnNewMail

bool Challenge_whale::OnNewMail(MOOSMSG_LIST &NewMail)
{
  MOOSMSG_LIST::iterator p;
   
  for(p=NewMail.begin(); p!=NewMail.end(); p++) {
    CMOOSMsg &msg = *p;

    //--------------------------------------------
    //BWSI added code
    std::string key = msg.GetKey();

    if (key.compare("NAV_X")==0) {
      _navX = msg.GetDouble();
    }
    else if (key.compare("NAV_Y")==0) {
      _navY = msg.GetDouble();
    }
    else if (key.compare("NAV_DEPTH")==0) {
      _navDepth = msg.GetDouble();
    }
    else if (key.compare("NAV_HEADING")==0) {
      _navHeading = msg.GetDouble();
    }
    else if (key.compare("NAV_SPEED")==0) {
      _navSpeed = msg.GetDouble();
    }
    else if (key.compare("NODE_REPORT")==0) {
      _nodeReports.push(msg.GetString());
    }
    else {
      std::cerr << "Unknown message type: " << key << std::endl;
    }
    //
    //-----------------------------------------

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

bool Challenge_whale::OnConnectToServer()
{
   RegisterVariables();
   return(true);
}

//---------------------------------------------------------
// Procedure: Iterate()
//            happens AppTick times per second

bool Challenge_whale::Iterate()
{
  //--------------------------------------------------
  //BWSI added code
  // Process the node reports that have come in since the last call to Iterate()
  if (_nodeReports.empty()) {
    _emptyCount++;
  }
  else {
    _emptyCount = 0;
  }

  if (_emptyCount > 25) {
    // make sure we're loitering
    Notify("ESCAPE", "false");
    Notify("PATROL", "true");
  }

  while (!_nodeReports.empty()) {
    std::string report = _nodeReports.front();

    // convert the report into a "dictionary"
    std::map<std::string, std::string> thisContact = ReadNodeReport(report);
    
    // check if this contact is in our list
    bool isNew = true;
    for (std::map<std::string, std::string>& contact : _contactList) {
      if (SameContact(contact, thisContact)) {
        // We already have a record of this contact, so update it
        //std::cout << "Known contact " << contact["NAME"] << ", updating..." << std::endl;
        for (std::map<std::string,std::string>::iterator it=contact.begin(); it!=contact.end();it++) {
          contact[it->first] = thisContact[it->first];
        }
        isNew = false;
        break;
      } 
    }
    // if it was not on our list, then add it
    if (isNew)
      _contactList.push_back(thisContact);

    // remove the report from the queue  
    _nodeReports.pop();
  }

  if (_isTagged)
    return(true);

  // loop through our contact list and decide what to do
  for (std::map<std::string, std::string> contact : _contactList) {
    double distance = sqrt(pow(std::stof(contact["X"]) - _navX, 2) + pow(std::stof(contact["Y"])-_navY,2));
    std::cout << "Dist = " << distance << " to " << contact["NAME"] << std::endl;
    
    // don't care about fellow non-players
    if (contact["GROUP"].compare("npc")==0) {
      continue;
    }

    double depth = std::stod(contact["DEP"]);
    std::cout << "depth = " << depth << std::endl;
    if (depth < 5.0) {
      // run away from surface craft
      if (distance < _minChaseDist) {
        // we've been tagged!
        std::cout << "TAGGED!" << std::endl;
        std::string msg = "SRC=" + contact["NAME"] + ",TYPE=" + contact["TYPE"] + ",GROUP=" + contact["GROUP"]+",WHALE=" + _myName;
        Notify("WHALE_TAGGED", msg);

        Notify("TAGGED_BY", contact["NAME"]);
        Notify("ESCAPE", "false");
        Notify("TAGGED", "true");
        _isTagged = true;
      }
      else if (distance < _maxChaseDist) {
        // run away!
        std::cout << "Dist = " << distance << ", run away from " << contact["NAME"] << "!" << std::endl;
        std::ostringstream message;
        message << "contact = " << contact["NAME"];
        Notify("AVOID_UPDATE", message.str());
        Notify("ESCAPE", "true");
        Notify("PATROL", "false");
      }
      else {
        Notify("PATROL", "true");
      }
    }
    else {
      ; //chase down a UUV
    }
  }
  //
  //---------------------------------------------------

  return(true);
}

//---------------------------------------------------------
// Procedure: OnStartUp()
//            happens before connection is open

bool Challenge_whale::OnStartUp()
{
  list<string> sParams;
  m_MissionReader.EnableVerbatimQuoting(false);
  if(m_MissionReader.GetConfiguration(GetAppName(), sParams)) {
    list<string>::iterator p;
    for(p=sParams.begin(); p!=sParams.end(); p++) {
      string line  = *p;
      string param = tolower(biteStringX(line, '='));
      string value = line;
      
      if(param == "max_chase_distance") {
        _maxChaseDist = std::stof(value);
        std::cout << "max = " << _maxChaseDist << std::endl;
      }
      else if(param == "min_chase_distance") {
        _minChaseDist = std::stof(value);
        std::cout << "min = " << _minChaseDist << std::endl;
      }
      else if(param == "name") {
        _myName = value;
      }
    }
  }
  
  RegisterVariables();	
  return(true);
}

//---------------------------------------------------------
// Procedure: RegisterVariables

void Challenge_whale::RegisterVariables()
{
  //--------------------------
  // BWSI added code
  Register("NAV_X", 0);
  Register("NAV_Y", 0);
  Register("NAV_DEPTH", 0);
  Register("NAV_HEADING", 0);
  Register("NAV_SPEED", 0);

  Register("NODE_REPORT", 0);
  // BWSI added code
  //--------------------------
}

