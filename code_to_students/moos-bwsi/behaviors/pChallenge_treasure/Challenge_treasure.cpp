/************************************************************/
/*    NAME:                                               */
/*    ORGN: MIT                                             */
/*    FILE: Challenge_treasure.cpp                                        */
/*    DATE:                                                 */
/************************************************************/

#include <iterator>
#include "MBUtils.h"
#include "Challenge_treasure.h"

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

Challenge_treasure::Challenge_treasure()
{
  _isPickedUp = false;
  _isCollected = false;
}

//---------------------------------------------------------
// Destructor

Challenge_treasure::~Challenge_treasure()
{
}

//---------------------------------------------------------
// Procedure: OnNewMail

bool Challenge_treasure::OnNewMail(MOOSMSG_LIST &NewMail)
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

bool Challenge_treasure::OnConnectToServer()
{
   RegisterVariables();
   return(true);
}

//---------------------------------------------------------
// Procedure: Iterate()
//            happens AppTick times per second

bool Challenge_treasure::Iterate()
{
  //--------------------------------------------------
  //BWSI added code
  // Process the node reports that have come in since the last call to Iterate()
  while (!_nodeReports.empty()) {
    std::string report = _nodeReports.front();
    std::cout << "Reading node report ... " << std::endl;

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
    double pickup_range = sqrt(pow(distance,2) + pow(std::stod(contact["DEP"])-_navDepth,2));
    std::cout << "Dist = " << distance << " to " << contact["NAME"] << std::endl;
    std::cout << "Range = " << pickup_range << " to " << contact["NAME"] << std::endl;
    
    if (pickup_range < 2*_minChaseDist) {
      // if it's been picked up already, it's either continuing or being stolen!
      if (_isPickedUp) {
        bool steal = true;
        for (std::map<std::string, std::string> coll : _contactsCollected ) {
          if (SameContact(coll, contact)) {
            steal = false;
            // continuing
            break;
          }
        }

        // Stolen by new vehicle!
        if (steal) {
          std::string msg = "contact = " + contact["NAME"];
          Notify("FOLLOW_UPDATES", msg);
          msg = contact["NAME"] + "," + contact["TYPE"] + "," + contact["GROUP"];
          Notify("STOLEN_BY", msg);
          _contactsCollected.push_back(contact);
        }
      }
      else {
        // first time treasure picked up
        _isPickedUp = true;
        // start following the UUV
        Notify("FOLLOW", "true");
        Notify("WAIT", "false");
        std::string msg = "contact = " + contact["NAME"];
        Notify("FOLLOW_UPDATES", msg);
      
        msg = "SRC=" + contact["NAME"] + ",TYPE=" + contact["TYPE"] + ",GROUP=" + contact["GROUP"]+",TREASURE=" + _myName;
        Notify("TREASURE_FOUND", msg);
        
        _contactsCollected.push_back(contact);
      }
    }

    // outside of min range we don't care.

    // see if we've been carried to the boundary
    double maxR = 1500;
    if ( (fabs(_navX)>maxR) || (fabs(_navY)>maxR) ) {
      _isCollected = true;

      std::string msg = "SRC=" + contact["NAME"] + ",TYPE=" + contact["TYPE"] + ",GROUP=" + contact["GROUP"]+",TREASURE=" + _myName;
      
      Notify("TREASURE_RECOVERED", msg);
      Notify("DEPLOY", "false");
      Notify("FOLLOW", "false");
      Notify("WAIT", "true");
    }
  }
  //
  //---------------------------------------------------

  return(true);
}

//---------------------------------------------------------
// Procedure: OnStartUp()
//            happens before connection is open

bool Challenge_treasure::OnStartUp()
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
    }
  }
  
  RegisterVariables();	
  return(true);
}

//---------------------------------------------------------
// Procedure: RegisterVariables

void Challenge_treasure::RegisterVariables()
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

