/************************************************************/
/*    NAME:                                               */
/*    ORGN: MIT                                             */
/*    FILE: Challenge_treasure.h                                          */
/*    DATE:                                                 */
/************************************************************/

#ifndef Challenge_treasure_HEADER
#define Challenge_treasure_HEADER

#include "MOOS/libMOOS/MOOSLib.h"
#include<queue>

class Challenge_treasure : public CMOOSApp
{
 public:
   Challenge_treasure();
   ~Challenge_treasure();

 protected: // Standard MOOSApp functions to overload  
   bool OnNewMail(MOOSMSG_LIST &NewMail);
   bool Iterate();
   bool OnConnectToServer();
   bool OnStartUp();

 protected:
   void RegisterVariables();

 private: // Configuration variables
  std::string _myName;
  double _minChaseDist;
  double _maxChaseDist;

 private: // State variables
  double _navX;
  double _navY;
  double _navDepth;
  double _navSpeed;
  double _navHeading;

  bool _isPickedUp;
  bool _isCollected;

  std::queue<std::string> _nodeReports;
  std::list<std::map<std::string, std::string> > _contactList;
  std::list<std::map<std::string, std::string> > _contactsCollected;
};

#endif 
