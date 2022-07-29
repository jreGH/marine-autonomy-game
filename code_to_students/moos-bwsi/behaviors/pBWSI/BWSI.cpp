/************************************************************/
/*    NAME:                                               */
/*    ORGN: MIT                                             */
/*    FILE: BWSI.cpp                                        */
/*    DATE:                                                 */
/************************************************************/

#include <iterator>
#include "MBUtils.h"
#include "BWSI.h"

using namespace std;

//---------------------------------------------------------
// Constructor

BWSI::BWSI()
{
}

//---------------------------------------------------------
// Destructor

BWSI::~BWSI()
{
}

//---------------------------------------------------------
// Procedure: OnNewMail

bool BWSI::OnNewMail(MOOSMSG_LIST &NewMail)
{
  MOOSMSG_LIST::iterator p;
   
  for(p=NewMail.begin(); p!=NewMail.end(); p++) {
    CMOOSMsg &msg = *p;

    // BWSI: added code
    std::string key = msg.GetKey();
    if (key.compare("NODE_REPORT")) {
      _nodeReports.push_back(msg.GetString());
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

bool BWSI::OnConnectToServer()
{
   RegisterVariables();
   return(true);
}

//---------------------------------------------------------
// Procedure: Iterate()
//            happens AppTick times per second

bool BWSI::Iterate()
{
  //----------------------------------------
  // BWSI added
  // process our node reports

  for (std::string report : _nodeReports) {
    std::map<std::string, std::string> this_map = parseNodeReport(report);

    // manage the node report: update, ignore or add to list
    // return true if it's a new contact
    bool isNewContact = manageContact(this_map);

    if (isNewContact) {
      //decide what to do about it

      if (this_map["type"].compare(_typeToFollow)) {
        // send to our following behavior update variable
        std::string follow_string = "contact = " + this_map["name"];
        Notify("FOLLOW_UPDATE", follow_string);
      }
    }


  }
  
  return(true);
}

//---------------------------------------------------------
// Procedure: OnStartUp()
//            happens before connection is open

bool BWSI::OnStartUp()
{
  list<string> sParams;
  m_MissionReader.EnableVerbatimQuoting(false);
  if(m_MissionReader.GetConfiguration(GetAppName(), sParams)) {
    list<string>::iterator p;
    for(p=sParams.begin(); p!=sParams.end(); p++) {
      string line  = *p;
      string param = tolower(biteStringX(line, '='));
      string value = line;
      
      // BWSI added
      if(param.compare("follow_type")) {
        _typeToFollow = value;
      }
      else if(param.compare("group")) {
        _myTeam = value;
      }
    }
  }
  
  RegisterVariables();	
  return(true);
}

//---------------------------------------------------------
// Procedure: RegisterVariables

void BWSI::RegisterVariables()
{
  // Register("FOOBAR", 0);
  //----------------------------------------
  // BWSI added
  Register("NODE_REPORT");
  Register("NAV_X");
  Register("NAV_Y");
  Register("NAV_DEPTH");
  Register("NAV_SPEED");
  //
  //-----------------------------------------
}

