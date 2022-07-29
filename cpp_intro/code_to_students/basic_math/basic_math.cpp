#include <cmath>
#include <iostream>

// calculate distance and heading between two points
int main()
{
    double distance, heading;
    double x2 = 10;
    double x1 = 5;
    double y1 = 100;
    double y2 = -50;

    distance = sqrt( pow(x2-x1, 2) + pow(y2-y1, 2) );
    std::cout << "Distance is " << distance << " meters." << std::endl;

    // calculate heading (CW from +y, in range 0->360 degrees)
    heading = fmod(atan2(x2-x1, y2-y1) / M_PI * 180.0 + 360.0, 360.0);
    std::cout << "Heading from 1 to 2 is  " << heading << " degrees." << std::endl;

    return 0;
}

