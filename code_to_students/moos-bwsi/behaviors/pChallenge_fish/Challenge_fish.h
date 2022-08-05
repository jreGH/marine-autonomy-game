/************************************************************/
/*    NAME:                                               */
/*    ORGN: MIT                                             */
/*    FILE: Challenge_fish.h                                          */
/*    DATE:                                                 */
/************************************************************/

#ifndef Challenge_fish_HEADER
#define Challenge_fish_HEADER

#include "MOOS/libMOOS/MOOSLib.h"
#include<queue>

class Challenge_fish : public CMOOSApp
{
 public:
   Challenge_fish();
   ~Challenge_fish();

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

  int _emptyCount;
  bool _isTagged;

  std::queue<std::string> _nodeReports;
  std::list<std::map<std::string, std::string> > _contactList;
  std::list<std::map<std::string, std::string> > _contactsCollected;
};

#endif 
