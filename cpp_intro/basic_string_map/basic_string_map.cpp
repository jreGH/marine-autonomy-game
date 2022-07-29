#include <cmath>
#include <string>
#include <iostream>
#include <sstream>
#include <vector>
#include <tuple>

template <typename T> void print_elem(const T& t) {
    std::cout << t ;
}

//using namespace std;

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


std::tuple<std::vector<std::string>, std::vector<std::string>> vectorFunction(std::string report) {

    std::vector<std::string> keys, values;

    // parsing a key=value string
	std::stringstream ss(report);
    std::string current_key;
	std::string current_value;

	while (std::getline(ss, current_key, '=')) {
        
        // return an error if there is no value after the "="
		if (!std::getline(ss, current_value, ',')) {
			std::cerr << "ERROR: no matching value " << std::endl;
           
            exit(-42);

		}
      // somehow add current_key to our vector of keys
       keys.push_back(current_key);
      // somehow add the current_value to the output vector "values"
       values.push_back(current_value);

	}

    return std::make_tuple(keys,values);

}

int main()
{
    double distance, heading;
    double x1 = 5;
    double y1 = 100;
    double x2 = 0, y2 = 0;
    std::vector<std::string> keys_out, values_out;

    std::string node_report = "NAME=otter,X=-164.52,Y=-21.94,SPD=4,HDG=307.04,DEP=0,LAT=1.28611202,LON=103.85384948,TYPE=kayak,COLOR=yellow,MODE=MODE@LOITERING_ONE,ALLSTOP=clear,INDEX=880,YAW=2.4950916,TIME=16581224369.98,LENGTH=4";

    std::tie(keys_out, values_out) = vectorFunction(node_report);
   
    while (keys_out.begin() != keys_out.end()) {
      //  std::cout << "Key: "; print_elem(keys_out.back()); std::cout << std::endl;
        std::cout << "Key: " << keys_out.back() << std::endl;
        std::cout << "Value: "; print_elem(values_out.back()); std::cout << std::endl;
        keys_out.pop_back();
        values_out.pop_back();
    }


    return 0;
}