/*****************************************************************/
/*    NAME: Joe Edwards                                          */
/*    ORGN: MIT BWSI                                             */
/*    FILE: Shape_Tuna.h                                         */
/*    DATE: 2022-07-19                                           */
/*                                                               */
/* This file is part of MOOS-IvP                                 */
/*                                                               */
/* MOOS-IvP is free software: you can redistribute it and/or     */
/* modify it under the terms of the GNU General Public License   */
/* as published by the Free Software Foundation, either version  */
/* 3 of the License, or (at your option) any later version.      */
/*                                                               */
/* MOOS-IvP is distributed in the hope that it will be useful,   */
/* but WITHOUT ANY WARRANTY; without even the implied warranty   */
/* of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See  */
/* the GNU General Public License for more details.              */
/*                                                               */
/* You should have received a copy of the GNU General Public     */
/* License along with MOOS-IvP.  If not, see                     */
/* <http://www.gnu.org/licenses/>.                               */
/*****************************************************************/

#ifndef SHAPE_TUNA_HEADER
#define SHAPE_TUNA_HEADER

double g_tunaBody[]=
{
109.93, 116.52,
87.69, 129.70,
68.62, 143.35,
59.73, 167.83,
49.13, 191.62,
36.12, 214.17,
20.99, 235.36,
2.61, 239.88,
-8.00, 243.35,
-26.06, 231.95,
-41.30, 210.83,
-53.52, 187.84,
-63.66, 163.86,
-72.12, 139.23,
-78.44, 113.96,
-93.95, 93.56,
-105.02, 70.22,
-93.58, 61.91,
-83.35, 53.77,
-80.79, 27.86,
-76.64, 2.15,
-78.69, -21.82,
-89.07, -45.48,
-90.61, -71.40,
-76.55, -71.34,
-58.62, -62.84,
-48.14, -86.69,
-36.97, -110.22,
-24.78, -133.23,
-33.40, -152.41,
-53.66, -168.77,
-69.31, -189.25,
-61.36, -198.95,
-38.12, -187.78,
-13.59, -179.03,
10.50, -178.62,
34.93, -187.66,
58.46, -198.25,
67.46, -190.32,
52.17, -169.70,
31.88, -153.38,
21.86, -134.40,
34.37, -111.56,
45.36, -87.95,
55.14, -63.80,
68.20, -51.08,
84.76, -66.05,
88.24, -40.48,
82.67, -15.13,
78.35, 8.80,
86.70, 33.48,
94.55, 58.32,
102.38, 83.16,
116.53, 104.93
};

unsigned int g_tunaBodySize = 54;
double       g_tunaScale    = 1.0;
double       g_tunaLength   = 443;


double  g_tunaCtrX = 0.0;
double  g_tunaCtrY = 0.0;

#endif










