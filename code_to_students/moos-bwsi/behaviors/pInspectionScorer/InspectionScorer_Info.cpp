#include <cstdlib>
#include "InspectionScorer_Info.h"
#include "ColorParse.h"
#include "ReleaseInfo.h"
using namespace std;

void showSynopsis() {
    blk("SYNOPSIS:                                                       ");
    blk("  pInspectionScorer runs on the shoreside community.           ");
    blk("  It tracks pipeline coverage and grades ANOMALY_REPORT        ");
    blk("  messages from student vehicles, maintaining a live           ");
    blk("  scoreboard published as INSPECTION_SCORE.                   ");
}

void showHelpAndExit() {
    blu("Usage: pInspectionScorer file.moos [OPTIONS]                   ");
    showSynopsis();
    blk("Options: --alias= --example/-e --help/-h --interface/-i        ");
    blk("         --version/-v                                           ");
    exit(0);
}

void showExampleConfigAndExit() {
    blu("pInspectionScorer Example MOOS Configuration                   ");
    blk("ProcessConfig = pInspectionScorer                              ");
    blk("{                                                               ");
    blk("  AppTick   = 4                                                 ");
    blk("  CommsTick = 4                                                 ");
    blk("  pipeline = label=cable_01,depth=30.0,                        ");
    blk("             points=-300,-80:-200,-130:-100,-180:0,-220         ");
    blk("  anomaly  = pipeline=cable_01,x=-100,y=-180,type=damage       ");
    blk("  coverage_radius     = 30.0                                    ");
    blk("  coverage_score      = 1000                                    ");
    blk("  coverage_threshold  = 0.8                                     ");
    blk("  anomaly_score       = 500                                     ");
    blk("  false_alarm_penalty = 100                                     ");
    blk("  report_tolerance    = 15.0                                    ");
    blk("}                                                               ");
    exit(0);
}

void showInterfaceAndExit() {
    blu("pInspectionScorer INTERFACE                                    ");
    showSynopsis();
    blk("SUBSCRIPTIONS: NODE_REPORT, ANOMALY_REPORT_<VNAME> (dynamic)  ");
    blk("PUBLICATIONS:  INSPECTION_SCORE, VIEW_POINT (confirmed marks)  ");
    exit(0);
}

void showReleaseInfoAndExit() {
    showReleaseInfo("pInspectionScorer", "gpl");
    exit(0);
}
