/************************************************************/
/*    NAME:                                               */
/*    ORGN: MIT                                             */
/*    FILE: Challenge_shoreside.h                                          */
/*    DATE:                                                 */
/************************************************************/

#ifndef Challenge_shoreside_HEADER
#define Challenge_shoreside_HEADER

#include "MOOS/libMOOS/MOOSLib.h"
#include "MOOS/libMOOS/Thirdparty/AppCasting/AppCastingMOOSApp.h"
#include <queue>
//#include <algorithm>

class Challenge_shoreside : public AppCastingMOOSApp
{
 public:
   Challenge_shoreside();
   ~Challenge_shoreside();

 protected: // Standard MOOSApp functions to overload  
   bool OnNewMail(MOOSMSG_LIST &NewMail);
   bool Iterate();
   bool OnConnectToServer();
   bool OnStartUp();

   bool buildReport();

 protected:
   void RegisterVariables();

 private: // Configuration variables
  int _whaleScore;
  int _fishScore;
  int _pickupScore;
  int _collectScore;
  int _biteTimeout;
  int _gameLengthMin;

 private: // State variables

  double _startTime;

  std::map<std::string, int> _teamScore;

  std::queue<std::string> _nodeReports;
  std::map<std::string, std::string> _contactList;
  std::queue<std::string> _whaleTags;
  std::queue<std::string> _fishPhotos;
  std::queue<std::string> _treasuresFound;
  std::queue<std::string> _treasuresRecovered;
  std::queue<std::string> _timeouts;
  std::queue<std::pair<std::string, double>> _timeoutList;
  std::vector<std::string> _teamNames;
  std::vector<int> _scores;
};

#endif 
