#include <cmath>
#include <string>
#include <iostream>
#include <sstream>

class MOOSPRocess {
    public:
        double get_distance();
        double get_heading();
        void read_node_report(std::string node_report) {

        }


    private:
        double _x;
        double _y;

        double _distance_from_me;
        double _heading_from_me;

        double calculate_distance_from_me(double x2, double y2) {
            _distance_from_me = sqrt( pow(x2-_x, 2) + pow(y2-_y, 2) );
        }

        double calculate_heading_from_me(double x2, double y2) {
            _heading_from_me = fmod(atan2(x2-_x, y2-_y) / M_PI * 180.0 + 360.0, 360.0);
        }
};

// This is a unit test of the calculate_distance function
int main()
{
    double distance, heading;
    double x1 = 5;
    double y1 = 100;
    double x2 = 0, y2 = 0;

    std::string node_report = "NAME=otter,X=-164.52,Y=-21.94,SPD=4,HDG=307.04,DEP=0,LAT=1.28611202,LON=103.85384948,TYPE=kayak,COLOR=yellow,MODE=MODE@LOITERING_ONE,ALLSTOP=clear,INDEX=880,YAW=2.4950916,TIME=16581224369.98,LENGTH=4";

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
            if (current_key == "X") {
                x2 = std::stof(current_value);
            }
            else if (current_key == "Y") {
                y2 = std::stof(current_value);
            }
		}
	}

    std::cout << "x2=" << x2 << ", y2=" << y2 << std::endl;

    distance = calculate_distance(x1, y1, x2, y2);
    std::cout << "Distance is " << distance << std::endl;

    heading = calculate_heading(x1, y1, x2, y2);
    std::cout << "Heading from 1 to 2 is  " << heading << " degrees." << std::endl;

    exit(0);
}