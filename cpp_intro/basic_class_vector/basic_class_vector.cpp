#include <cmath>
#include <string>
#include <iostream>
#include <sstream>
#include <vector>

class NodeReport {
    public:
        std::string _name;
        double _x;
        double _y;
        double _speed;
        double _heading;
        double _depth;
        double _lat;
        double _lon;
        double _time;
        std::string _type;
        
        void parse_node_report(std::string node_report) {
            // parsing a key=value string
	        std::stringstream ss(node_report);
            std::string current_key;
	        std::string current_value;

	        while (std::getline(ss, current_key, '=')) {
                // add key to our vector of keys
		        std::cout << "current key = " << current_key << std::endl;

                // return an error if there is no value after the "="
		        if (!std::getline(ss, current_value, ',')) {
			        std::cerr << "ERROR: no matching value " << std::endl;
		        }
		        else {
			        std::cout << "current value = " << current_value << std::endl;
                    if (current_key == "X")
                        _x = std::stof(current_value);
                    else if (current_key == "Y")
                        _y = std::stof(current_value);
                    else if (current_key == "NAME")
                        _name = current_value;
                    else if (current_key == "type")
                        _type = current_value;
                    else if (current_key == "TIME")
                        _time = std::stof(current_value);
                }

	        }
            std::cout << "x is now " << _x << ", y is now " << _y << std::endl;
        }

        bool is_same(NodeReport nr) {
            return (nr._name == _name && nr._type == _type);
        }

        void update(NodeReport nr) {
            if (!is_same(nr) || (_time >= nr._time))
                return;

            _x = nr._x;
            _y = nr._y;
            _time = nr._time;


        }
};

double calculate_distance(double x1, double y1, double x2, double y2)
{
    double distance = sqrt( pow(x2-x1, 2) + pow(y2-y1, 2) );

    return distance;
}

double calculate_heading(double x1, double y1, double x2, double y2)
{
    double heading = fmod(atan2(x2-x1, y2-y1) / M_PI * 180.0 + 360.0, 360.0);

    return heading;
}

// This is a unit test of the calculate_distance function
int main()
{
    double distance, heading;
    double x1 = 5;
    double y1 = 100;
    double x2 = 0, y2 = 0;
    std::vector<NodeReport> nodeReports;
    NodeReport currentReport;

    std::vector<std::string> node_reports;
    node_reports.push_back("NAME=otter,X=-164.52,Y=-21.94,SPD=4,HDG=307.04,DEP=0,LAT=1.28611202,LON=103.85384948,TYPE=kayak,COLOR=yellow,MODE=MODE@LOITERING_ONE,ALLSTOP=clear,INDEX=880,YAW=2.4950916,TIME=16581224369.98,LENGTH=4");
    node_reports.push_back("NAME=jellyfish,X=5,Y=-10,SPD=4,HDG=25,DEP=5,LAT=1.28611202,LON=103.85384948,TYPE=auv,COLOR=yellow,MODE=MODE@LOITERING_ONE,ALLSTOP=clear,INDEX=880,YAW=2.4950916,TIME=16581224369.98,LENGTH=4");
    node_reports.push_back("NAME=squid,X=-164.52,Y=-21.94,SPD=4,HDG=307.04,DEP=0,LAT=1.28611202,LON=103.85384948,TYPE=kayak,COLOR=yellow,MODE=MODE@LOITERING_ONE,ALLSTOP=clear,INDEX=880,YAW=2.4950916,TIME=16581224369.98,LENGTH=4");
    node_reports.push_back("NAME=otter,X=-164.52,Y=-21.94,SPD=4,HDG=307.04,DEP=0,LAT=1.28611202,LON=103.85384948,TYPE=kayak,COLOR=yellow,MODE=MODE@LOITERING_ONE,ALLSTOP=clear,INDEX=880,YAW=2.4950916,TIME=16581224369.98,LENGTH=4");
    node_reports.push_back("NAME=otter,X=-164.52,Y=-21.94,SPD=4,HDG=307.04,DEP=0,LAT=1.28611202,LON=103.85384948,TYPE=kayak,COLOR=yellow,MODE=MODE@LOITERING_ONE,ALLSTOP=clear,INDEX=880,YAW=2.4950916,TIME=16581224369.98,LENGTH=4");


    // loop over node_reports
    for (std::string node_report : node_reports) {
        currentReport.parse_node_report(node_report);

        // check to see if this one is a new report
        bool is_new = true;
        for (NodeReport nodeReport : nodeReports) {
            if (nodeReport.is_same(currentReport)) {
                nodeReport.update(currentReport);
                is_new = false;
            }
        }

        if (is_new)
            nodeReports.push_back(currentReport);
    }   
    

    x2 = nodeReport._x;
    y2 = nodeReport._y;
    std::cout << "x2=" << x2 << ", y2=" << y2 << std::endl;

    distance = calculate_distance(x1, y1, x2, y2);
    std::cout << "Distance is " << distance << std::endl;

    heading = calculate_heading(x1, y1, x2, y2);
    std::cout << "Heading from 1 to 2 is  " << heading << " degrees." << std::endl;

    return 0;
}