/************************************************************/
/*    NAME:                                               */
/*    ORGN: MIT                                             */
/*    FILE: Challenge_fish.cpp                                        */
/*    DATE:                                                 */
/************************************************************/

#include <iterator>
#include "MBUtils.h"
#include "Challenge_fish.h"

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

Challenge_fish::Challenge_fish()
{
  _isTagged = false;
}

//---------------------------------------------------------
// Destructor

Challenge_fish::~Challenge_fish()
{
}

//---------------------------------------------------------
// Procedure: OnNewMail

bool Challenge_fish::OnNewMail(MOOSMSG_LIST &NewMail)
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

bool Challenge_fish::OnConnectToServer()
{
   RegisterVariables();
   return(true);
}

//---------------------------------------------------------
// Procedure: Iterate()
//            happens AppTick times per second

bool Challenge_fish::Iterate()
{
  //--------------------------------------------------
  //BWSI added code
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

  // Process the node reports that have come in since the last call to Iterate()
  while (!_nodeReports.empty()) {
    std::cout << "Reading node report..." << std::endl;
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

    std::cout << "contact list is " << _contactList.size() << " long" << std::endl;

    // remove the report from the queue  
    _nodeReports.pop();
  }

  // loop through our contact list and decide what to do
  for (std::map<std::string, std::string> contact : _contactList) {
    double distance = sqrt(pow(std::stof(contact["X"]) - _navX, 2) + pow(std::stof(contact["Y"])-_navY,2));
    double photo_range = sqrt(pow(distance,2) + pow(std::stod(contact["DEP"])-_navDepth,2));
    
    std::cout << "distance = " << distance << ", photo_range = " << photo_range << std::endl;
    std::cout << "_navdepth = " << _navDepth << ", depth = " << contact["DEP"] << std::endl;
    if ((photo_range < 2*_minChaseDist) && (!_isTagged)) {
      // photographed
      std::string msg = "SRC=" + contact["NAME"] + ",TYPE=" + contact["TYPE"] + ",GROUP=" + contact["GROUP"]+",FISH=" + _myName;
      Notify("FISH_PHOTOED", msg);
      Notify("ESCAPE", "false");
      Notify("TAGGED", "true");

      _isTagged = true;
      _contactsCollected.push_back(contact);
    }
    else if (distance > _maxChaseDist) {
      // call off the chase
      Notify("ESCAPE", "false");
      Notify("PATROL", "true");
    }
    else if (distance < _maxChaseDist) {
      if (!_isTagged) {
        // if we haven't been photographed yet
        std::ostringstream message;
        message << "contact = " << contact["NAME"];
        Notify("AVOID_UPDATES", message.str());
        Notify("ESCAPE", "true");
        Notify("PATROL", "false");
      }
    }
  }
  //
  //---------------------------------------------------

  return(true);
}

//---------------------------------------------------------
// Procedure: OnStartUp()
//            happens before connection is open

bool Challenge_fish::OnStartUp()
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
      }
      else if(param == "min_chase_distance") {
        _minChaseDist = std::stof(value);
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

void Challenge_fish::RegisterVariables()
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

