/************************************************************/
/*    FILE: InfrastructureSensor_Info.cpp                   */
/*    ORGN: BWSI AUVC                                       */
/************************************************************/

#include <cstdlib>
#include <iostream>
#include "InfrastructureSensor_Info.h"
#include "ColorParse.h"
#include "ReleaseInfo.h"

using namespace std;

void showSynopsis()
{
    blk("SYNOPSIS:                                                       ");
    blk("------------------------------------                            ");
    blk("  pInfrastructureSensor runs on the shoreside community.       ");
    blk("  It knows the ground-truth geometry of undersea pipelines or  ");
    blk("  cables and anomaly positions along them.  Each iteration it  ");
    blk("  simulates a forward-looking sonar for every known vehicle    ");
    blk("  and publishes detection reports when the sensor model fires. ");
    blk("                                                                ");
    blk("  Detection reports are published as:                          ");
    blk("    INFRASTRUCTURE_DETECT_<VNAME>                              ");
    blk("  and must be bridged to vehicle communities via pShare.       ");
}

void showHelpAndExit()
{
    blk("                                                                ");
    blu("=============================================================== ");
    blu("Usage: pInfrastructureSensor file.moos [OPTIONS]               ");
    blu("=============================================================== ");
    blk("                                                                ");
    showSynopsis();
    blk("                                                                ");
    blk("Options:                                                        ");
    mag("  --alias","=<ProcessName>                                      ");
    blk("      Launch with the given process name.                       ");
    mag("  --example, -e                                                 ");
    blk("      Display example MOOS configuration block.                 ");
    mag("  --help, -h                                                    ");
    blk("      Display this help message.                                ");
    mag("  --interface, -i                                               ");
    blk("      Display MOOS publications and subscriptions.              ");
    mag("  --version,-v                                                  ");
    blk("      Display the release version.                              ");
    blk("                                                                ");
    exit(0);
}

void showExampleConfigAndExit()
{
    blk("                                                                ");
    blu("=============================================================== ");
    blu("pInfrastructureSensor Example MOOS Configuration               ");
    blu("=============================================================== ");
    blk("                                                                ");
    blk("ProcessConfig = pInfrastructureSensor                          ");
    blk("{                                                               ");
    blk("  AppTick   = 4                                                 ");
    blk("  CommsTick = 4                                                 ");
    blk("                                                                ");
    blk("  // Define one or more pipelines / cables.                    ");
    blk("  // points = x1,y1:x2,y2:... (local XY metres)               ");
    blk("  pipeline = label=cable_01,depth=30.0,\\                      ");
    blk("             points=-300,-100:-200,-150:-100,-200:0,-220       ");
    blk("                                                                ");
    blk("  // Anomaly positions along a named pipeline.                 ");
    blk("  anomaly  = pipeline=cable_01,x=-100,y=-200,type=damage       ");
    blk("  anomaly  = pipeline=cable_01,x=50,y=-210,type=corrosion      ");
    blk("                                                                ");
    blk("  // Sensor model                                               ");
    blk("  detect_range  = 30.0    // max sensor range (m)              ");
    blk("  detect_cone   = 60.0    // half-angle of forward cone (deg)  ");
    blk("  noise_sigma   = 3.0     // position noise on reports (m)     ");
    blk("  p_false_alarm = 0.02    // false alarm rate per vehicle/s    ");
    blk("  reveal_pipe   = false   // show pipe in viewer when detected  ");
    blk("}                                                               ");
    blk("                                                                ");
    exit(0);
}

void showInterfaceAndExit()
{
    blk("                                                                ");
    blu("=============================================================== ");
    blu("pInfrastructureSensor INTERFACE                                ");
    blu("=============================================================== ");
    blk("                                                                ");
    showSynopsis();
    blk("                                                                ");
    blk("SUBSCRIPTIONS:                                                  ");
    blk("------------------------------------                            ");
    blk("  NODE_REPORT  — vehicle position/heading from all communities  ");
    blk("                                                                ");
    blk("PUBLICATIONS (shoreside, bridged to vehicles via pShare):       ");
    blk("------------------------------------                            ");
    blk("  INFRASTRUCTURE_DETECT_<VNAME>                                ");
    blk("    pipeline=<label>,x=<f>,y=<f>,depth=<f>,type=<pipe|anomaly|false_alarm>,range=<f>");
    blk("    [,anomaly_type=<damage|corrosion|obstruction|...>]          ");
    blk("                                                                ");
    blk("PUBLICATIONS (shoreside viewer):                                ");
    blk("------------------------------------                            ");
    blk("  VIEW_SEGLIST — pipeline outline (when reveal_pipe=true)       ");
    blk("  VIEW_POINT   — anomaly marker when first detected             ");
    blk("                                                                ");
    exit(0);
}

void showReleaseInfoAndExit()
{
    showReleaseInfo("pInfrastructureSensor", "gpl");
    exit(0);
}
