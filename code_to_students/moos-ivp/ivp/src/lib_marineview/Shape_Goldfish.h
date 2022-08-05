/*****************************************************************/
/*    NAME: Michael Benjamin                                     */
/*    ORGN: Dept of Mechanical Eng / CSAIL, MIT Cambridge MA     */
/*    FILE: Shape_Kayak.h                                        */
/*    DATE: September 21st 2007                                  */
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

#ifndef SHAPE_GOLDFISH_HEADER
#define SHAPE_GOLDFISH_HEADER

double g_goldfishBody[]=
{
    0.0,      0.0,     
    5.25,     6.0,
    7.25,     9.0,      
    8.75,    12.0,
   12.0,     20.0,      
   13.25,    26.0, 
   14.00,    32.0,     
   14.625,   40.0,
   14.625,   42.0,     
   14.875,   48.0, 
   15.0,     54.0,     
   14.875,   60.0, 
   14.5,     66.0,     
   13.875,   72.0, 
   13.75,    78.0,     
   12.5,     84.0, 
   11.375,   90.0,     
   10.375,   96.0, 
    9.25,   100.0,    
    7.875,  104.0, 
    6.50,   108.0,    
    5.375,  112.0, 
    3.375,  116.0,    
    2.375,  118.0, 
    2.0,    119.0,     
    1.5,    119.5,
    1.0,    119.75,    
    0.5,    119.875,
   -0.5,    119.875,  
   -1.0,    119.75, 
   -1.5,    119.5, 
   -2.0,    119.0,
   -2.375,  118.0,  
   -3.375,  116.0, 
   -5.375,  112.0,  
   -6.50,   108.0, 
   -7.875,  104.0,  
   -9.25,   100.0, 
  -10.375,   96.0,   
  -11.375,   90.0, 
  -12.5,     84.0,  
  -13.75,    78.0, 
  -13.875,   72.0,  
  -14.5,     66.0, 
  -14.875,   60.0,  
  -15.0,     54.0, 
  -14.875,   48.0,    
  -14.625,   42.0,
  -14.625,   40.0,    
  -14.00,    32.0, 
  -13.25,    26.0,    
  -12.0,     20.0, 
  -8.75,     12.0,    
  -7.25,      9.0,    
  -5.25,      6.0,   
   0.0,       0.0
};
unsigned int g_goldfishBodySize = 56;
double       g_goldfishScale    = 1.0;
double       g_goldfishLength   = 119.875;

double  g_goldfishCtrX = 0.0;
double  g_goldfishCtrY = 59.9375;

#endif










