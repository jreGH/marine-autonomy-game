#include <cmath>
#include <iostream>

double calculate_distance(double x1, double y1, double x2, double y2)
{

// add code here that will calculate distance between points (x1, y1) and (x2, y2) return the value as a double

}

// write another function named calculate_heading 
// input variables: x1, y1, x2, y2
// return heading that is type double

// add code here 

// This is a unit test of the calculate_distance function
int main()
{
    double distance, heading;
    double x1 = 0;
    double x2 = -50;
    double y1 = 0;
    double y2 = -50;

    distance = calculate_distance(x1, y1, x2, y2);
    std::cout << "Distance is " << distance << std::endl;

    heading = calculate_heading(x1, y1, x2, y2);
    std::cout << "Heading from 1 to 2 is  " << heading << " degrees." << std::endl;


    return 0;
}