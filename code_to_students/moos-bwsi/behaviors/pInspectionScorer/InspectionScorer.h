/************************************************************/
/*    FILE: InspectionScorer.h                              */
/*    ORGN: BWSI AUVC                                       */
/*                                                          */
/*    Shoreside referee for the infrastructure inspection   */
/*    mission.  Tracks two independent metrics:             */
/*                                                          */
/*    1. COVERAGE — what fraction of each pipeline has      */
/*       been "seen" by at least one team vehicle passing   */
/*       within coverage_radius metres.                     */
/*                                                          */
/*    2. ANOMALY REPORTS — when a vehicle publishes         */
/*       ANOMALY_REPORT_<VNAME>, compare reported position  */
/*       to ground truth.  Award anomaly_score for a true   */
/*       positive; deduct false_alarm_penalty for clutter.  */
/*                                                          */
/*    Config (in shoreside.moos — mirrors pInfrastructure-  */
/*    Sensor, so add the same pipeline/anomaly lines):      */
/*      pipeline = label=cable_01,depth=30.0,               */
/*                 points=x0,y0:x1,y1:...                   */
/*      anomaly  = pipeline=cable_01,x=...,y=...,type=...   */
/*      coverage_radius    = 30.0   // metres               */
/*      coverage_score     = 1000   // max pts for 100%     */
/*      coverage_threshold = 0.8    // fraction for max pts */
/*      anomaly_score      = 500    // pts per correct hit  */
/*      false_alarm_penalty= 100    // pts deducted per FP  */
/*      report_tolerance   = 15.0   // match radius (m)     */
/*      sample_step        = 5.0    // coverage grid (m)    */
/*                                                          */
/*    Publishes:                                            */
/*      INSPECTION_SCORE     — JSON-like leaderboard string */
/*      INSPECTION_COVERAGE  — per-team coverage fraction   */
/************************************************************/
#pragma once

#include "MOOS/libMOOS/MOOSLib.h"
#include "MOOS/libMOOS/Thirdparty/AppCasting/AppCastingMOOSApp.h"

#include <map>
#include <set>
#include <string>
#include <utility>
#include <vector>

class InspectionScorer : public AppCastingMOOSApp {
public:
    InspectionScorer();
    ~InspectionScorer() {}

protected:
    bool OnNewMail(MOOSMSG_LIST& NewMail);
    bool Iterate();
    bool OnConnectToServer();
    bool OnStartUp();
    bool buildReport();

    void RegisterVariables();

private:
    // ---- Geometry (parsed from config) ----
    struct Pipeline {
        std::string label;
        double      depth;
        std::vector<std::pair<double,double>> points;
    };

    struct Anomaly {
        std::string pipeline_label;
        double      x, y;
        std::string type;
    };

    // Precomputed sample grid for coverage tracking
    struct SamplePoint {
        double x, y;
    };

    // ---- Per-team state ----
    struct TeamState {
        std::string name;
        // Covered sample indices per pipeline: pipeline_label → set<sample_idx>
        std::map<std::string, std::set<size_t>> covered;
        // Anomaly claims: anomaly_idx → true if this team claimed it correctly
        std::map<size_t, bool> anomalyClaimed;
        int falseAlarms;
        int totalScore;
        TeamState() : falseAlarms(0), totalScore(0) {}
    };

    // ---- Vehicle → team mapping (learned from NODE_REPORT) ----
    std::map<std::string, std::string> _vehicleTeam;  // vname → team

    // ---- Ground truth ----
    std::vector<Pipeline> _pipelines;
    std::vector<Anomaly>  _anomalies;

    // Sample grid: pipeline_label → vector<SamplePoint>
    std::map<std::string, std::vector<SamplePoint>> _samples;

    // Per-team state
    std::map<std::string, TeamState> _teams;

    // Set of ANOMALY_REPORT_* variables we've already subscribed to
    std::set<std::string> _registeredReportVars;

    // ---- Config params ----
    double _coverageRadius;     // metres — matches sensor detect_range
    double _coverageScore;      // max score for 100% coverage
    double _coverageThreshold;  // fraction at which full coverage_score is awarded
    double _anomalyScore;       // points per correctly placed anomaly report
    double _falseAlarmPenalty;  // points deducted per false positive
    double _reportTolerance;    // max distance (m) for a report to count as TP
    double _sampleStep;         // grid spacing (m) for pipeline coverage sampling

    // ---- Helpers ----
    bool parsePipelineSpec(const std::string& spec);
    bool parseAnomalySpec(const std::string& spec);
    void buildSampleGrid();

    void processNodeReport(const std::string& raw);
    void processAnomalyReport(const std::string& raw, const std::string& vname);

    void updateCoverage(const std::string& team,
                        double vx, double vy);

    int computeTeamScore(const TeamState& ts) const;

    std::string getField(const std::string& str,
                         const std::string& key) const;

    std::string toUpper(const std::string& s) const;
    std::string toLower(const std::string& s) const;

    void publishScoreboard();
};
