/*****************************************************************/
/*    NAME: Joe Edwards                                          */
/*    ORGN: MIT BWSI                                             */
/*    FILE: Shape_Nemo.h	                                     */
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

#ifndef SHAPE_NEMO_HEADER
#define SHAPE_NEMO_HEADER

double g_nemoBody[]=
{
156, 198,
153, 211,
145, 223,
136, 235,
125, 243,
110, 240,
98, 235,
84, 230,
72, 222,
61, 215,
56, 197,
53, 182,
53, 173,
63, 159,
80, 152,
103, 153,
128, 158,
151, 174,
156, 187,
158, 195,
163, 189,
165, 179,
159, 167,
149, 154,
136, 145,
113, 146,
90, 146,
70, 149,
58, 155,
52, 163,
49, 154,
41, 144,
38, 130,
47, 141,
47, 129,
46, 114,
53, 103,
62, 85,
76, 84,
83, 92,
80, 108,
76, 123,
90, 117,
107, 117,
126, 127,
143, 136,
147, 125,
159, 124,
164, 137,
174, 141,
180, 151,
171, 163,
178, 155,
182, 142,
184, 131,
185, 119,
172, 126,
157, 114,
143, 107,
123, 105,
107, 103,
95, 104,
100, 93,
112, 84,
122, 80,
130, 88,
142, 95,
154, 97,
167, 105,
175, 109,
179, 100,
168, 97,
152, 92,
144, 86,
139, 75,
136, 86,
138, 67,
144, 55,
154, 49,
167, 45,
185, 52,
196, 65,
200, 81,
190, 92
};

unsigned int g_nemoBodySize = 84;
double       g_nemoScale    = 1.0;
double       g_nemoLength   = 200;


double  g_nemoCtrX = 90.0;
double  g_nemoCtrY = 80.0;

#endif










