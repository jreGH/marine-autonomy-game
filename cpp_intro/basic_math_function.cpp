#include <cmath>
#include <iostream>

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
    double x1 = 0;
    double x2 = -50;
    double y1 = 0;
    double y2 = -50;

    distance = calculate_distance(x1, y1, x2, y2);
    std::cout << "Distance is " << distance << std::endl;

    heading = calculate_heading(x1, y1, x2, y2);
    std::cout << "Heading from 1 to 2 is  " << heading << " degrees." << std::endl;


    exit(0);
}