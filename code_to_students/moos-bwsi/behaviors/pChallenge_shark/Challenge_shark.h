/************************************************************/
/*    NAME:                                               */
/*    ORGN: MIT                                             */
/*    FILE: Challenge_shark.h                                          */
/*    DATE:                                                 */
/************************************************************/

#ifndef Challenge_shark_HEADER
#define Challenge_shark_HEADER

#include "MOOS/libMOOS/MOOSLib.h"
#include<queue>
#include<limits>

class Challenge_shark : public CMOOSApp
{
 public:
   Challenge_shark();
   ~Challenge_shark();

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

  double _chaseStart;
  double _recoveryTime;
  bool _chasing;
  bool _recovering;


  std::queue<std::string> _bittenVehicles;
  std::queue<std::string> _nodeReports;
  std::list<std::map<std::string, std::string> > _contactList;
  std::list<std::map<std::string, std::string> > _contactsCollected;
};

#endif 
