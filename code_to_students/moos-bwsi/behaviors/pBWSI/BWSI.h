/************************************************************/
/*    NAME:                                               */
/*    ORGN: MIT                                             */
/*    FILE: BWSI.h                                          */
/*    DATE:                                                 */
/************************************************************/

#ifndef BWSI_HEADER
#define BWSI_HEADER

#include "MOOS/libMOOS/MOOSLib.h"

class BWSI : public CMOOSApp
{
 public:
   BWSI();
   ~BWSI();

 protected: // Standard MOOSApp functions to overload  
   bool OnNewMail(MOOSMSG_LIST &NewMail);
   bool Iterate();
   bool OnConnectToServer();
   bool OnStartUp();

 protected:
   void RegisterVariables();

 private: // Configuration variables

 private: // State variables
    //--------------------------------------------
    // BWSI added
    // the node report strings
    std::vector<std::string> _nodeReports;
    // our node report dictionaries of active contacts
    std::vector<std::map<std::string, std::string>> _activeContacts;
    // type of contacts we will follow
    std::string _typeToFollow;
    std::string _myTeam;
    //
    //--------------------------------------------
};

#endif 
