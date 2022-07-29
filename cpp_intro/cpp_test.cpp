#include <stdlib.h>
#include <string>
#include <math.h>
#include <iostream> 
#include <sstream>
#include <vector>

int main(int argc, char *argv[]){
	std::string my_string = "name=bob, age=23, class=bwsi";
	std::vector<std::string> keys;
	std::vector<std::string> vals;

	std::stringstream ss(my_string);
	std::string current_value;

	while (getline(ss, current_value, '=')) {
		keys.push_back(current_value);
		std::cout << "curent key = " << current_value << std::endl;

		if (!getline(ss, current_value, ',')) {
			std::cerr << "ERROR: no matching value " << std::endl;
		}
		else {
			vals.push_back(current_value);
			std::cout << "current value = " << current_value << std::endl;
		}
	}
}
