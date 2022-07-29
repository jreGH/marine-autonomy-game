#include <cmath>
#include <string>
#include <iostream>
#include <sstream>
#include <tuple>

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

std::tuple<double, double> extractXY_NodeReport(std::string s) {
       // parsing a key=value string
	std::stringstream ss(s);
    std::string current_key;
	std::string current_value;
    double x2, y2;

	while (std::getline(ss, current_key, '=')) {
        
        // print current_key to standard output 
		std::cout << "current key = " << current_key << std::endl;

        // return an error if there is no value after the "="
		if (!std::getline(ss, current_value, ',')) {
			std::cerr << "ERROR: no matching value " << std::endl;
		}
		else {
        //print current_value to standard output
			std::cout << "current value = " << current_value << std::endl;
            
            // assign values to X and Y 
            if (current_key == "X") {
                x2 = std::stod(current_value);
            }
            else if (current_key == "Y") {
                y2 = std::stod(current_value);
            }
		}
	}
   return std::make_tuple(x2,y2);

}


int main()
{
    double distance, heading;
    double x1 = 5;
    double y1 = 100;
    double x2 = 0, y2 = 0;

    std::string node_report = "NAME=otter,X=-164.52,Y=-21.94,SPD=4,HDG=307.04,DEP=0,LAT=1.28611202,LON=103.85384948,TYPE=kayak,COLOR=yellow,MODE=MODE@LOITERING_ONE,ALLSTOP=clear,INDEX=880,YAW=2.4950916,TIME=16581224369.98,LENGTH=4";

    std::tie(x2, y2) = extractXY_NodeReport(node_report);
   
    // print x2 and y2 to standard output 
    std::cout << "x2=" << x2 << ", y2=" << y2 << std::endl;

    distance = calculate_distance(x1, y1, x2, y2);
    std::cout << "Distance is " << distance << std::endl;

    heading = calculate_heading(x1, y1, x2, y2);
    std::cout << "Heading from 1 to 2 is  " << heading << " degrees." << std::endl;

    return 0;
}