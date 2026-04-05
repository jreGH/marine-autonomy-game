/************************************************************/
/*    FILE: InspectionScorer.cpp                            */
/*    ORGN: BWSI AUVC                                       */
/************************************************************/

#include "InspectionScorer.h"
#include "MBUtils.h"

#include <cmath>
#include <iomanip>
#include <sstream>

using namespace std;

// ============================================================
// Constructor
// ============================================================

InspectionScorer::InspectionScorer()
    : _coverageRadius(30.0),
      _coverageScore(1000.0),
      _coverageThreshold(0.8),
      _anomalyScore(500.0),
      _falseAlarmPenalty(100.0),
      _reportTolerance(15.0),
      _sampleStep(5.0)
{}


// ============================================================
// MOOS lifecycle
// ============================================================

bool InspectionScorer::OnConnectToServer()
{
    RegisterVariables();
    return true;
}

bool InspectionScorer::OnStartUp()
{
    AppCastingMOOSApp::OnStartUp();

    STRING_LIST sParams;
    m_MissionReader.EnableVerbatimQuoting(false);
    if (!m_MissionReader.GetConfiguration(GetAppName(), sParams))
        reportConfigWarning("No config block found for " + GetAppName());

    for (auto& line : sParams) {
        string param = tolower(biteStringX(line, '='));
        string val   = line;

        if      (param == "pipeline")           parsePipelineSpec(val);
        else if (param == "anomaly")            parseAnomalySpec(val);
        else if (param == "coverage_radius")    _coverageRadius    = atof(val.c_str());
        else if (param == "coverage_score")     _coverageScore     = atof(val.c_str());
        else if (param == "coverage_threshold") _coverageThreshold = atof(val.c_str());
        else if (param == "anomaly_score")      _anomalyScore      = atof(val.c_str());
        else if (param == "false_alarm_penalty")_falseAlarmPenalty = atof(val.c_str());
        else if (param == "report_tolerance")   _reportTolerance   = atof(val.c_str());
        else if (param == "sample_step")        _sampleStep        = atof(val.c_str());
        else
            reportUnhandledConfigWarning(param);
    }

    buildSampleGrid();
    RegisterVariables();
    return true;
}

void InspectionScorer::RegisterVariables()
{
    AppCastingMOOSApp::RegisterVariables();
    Register("NODE_REPORT", 0);
}


// ============================================================
// Mail
// ============================================================

bool InspectionScorer::OnNewMail(MOOSMSG_LIST& NewMail)
{
    AppCastingMOOSApp::OnNewMail(NewMail);

    for (auto& msg : NewMail) {
        const string& key = msg.GetKey();

        if (key == "NODE_REPORT") {
            processNodeReport(msg.GetString());
        }
        else if (strBegins(key, "ANOMALY_REPORT_")) {
            // Key format: ANOMALY_REPORT_JELLYFISH
            // Extract vehicle name from key suffix (lower-case)
            string vname = tolower(key.substr(15));  // after "ANOMALY_REPORT_"
            processAnomalyReport(msg.GetString(), vname);
        }
    }
    return true;
}

void InspectionScorer::processNodeReport(const string& raw)
{
    string vname = tolower(getField(raw, "NAME"));
    string group = tolower(getField(raw, "GROUP"));
    double vx    = atof(getField(raw, "X").c_str());
    double vy    = atof(getField(raw, "Y").c_str());

    if (vname.empty() || group.empty())
        return;

    // Map vehicle to team (create team record on first sight)
    _vehicleTeam[vname] = group;
    if (_teams.find(group) == _teams.end()) {
        TeamState ts;
        ts.name = group;
        _teams[group] = ts;
    }

    // Lazily subscribe to this vehicle's anomaly report variable
    string vname_upper = toUpper(vname);
    string report_var  = "ANOMALY_REPORT_" + vname_upper;
    if (_registeredReportVars.find(report_var) == _registeredReportVars.end()) {
        Register(report_var, 0);
        _registeredReportVars.insert(report_var);
    }

    // Update coverage for this team
    updateCoverage(group, vx, vy);
}

void InspectionScorer::processAnomalyReport(const string& raw,
                                             const string& vname)
{
    auto team_it = _vehicleTeam.find(vname);
    if (team_it == _vehicleTeam.end())
        return;
    string team = team_it->second;

    double rx = atof(getField(raw, "x").c_str());
    double ry = atof(getField(raw, "y").c_str());

    // Find the closest ground-truth anomaly within tolerance
    double bestDist = 1e9;
    int    bestIdx  = -1;
    for (size_t i = 0; i < _anomalies.size(); ++i) {
        double dx = _anomalies[i].x - rx;
        double dy = _anomalies[i].y - ry;
        double d  = sqrt(dx*dx + dy*dy);
        if (d < bestDist) { bestDist = d; bestIdx = (int)i; }
    }

    TeamState& ts = _teams[team];

    if (bestIdx >= 0 && bestDist <= _reportTolerance) {
        // True positive — but only if not already claimed by this team
        if (!ts.anomalyClaimed[(size_t)bestIdx]) {
            ts.anomalyClaimed[(size_t)bestIdx] = true;

            // Confirm in viewer with a green marker
            ostringstream pt;
            pt << fixed << setprecision(1);
            pt << "x=" << rx << ",y=" << ry
               << ",label=confirmed_" << team << "_" << bestIdx
               << ",color=lime,vertex_size=10,vertex_style=square";
            Notify("VIEW_POINT", pt.str());

            reportEvent("Anomaly confirmed for team " + team
                        + " at (" + doubleToString(rx,1)
                        + ", " + doubleToString(ry,1) + ")");
        }
    } else {
        ts.falseAlarms++;
        reportEvent("False alarm from team " + team
                    + " at (" + doubleToString(rx,1)
                    + ", " + doubleToString(ry,1) + ")");
    }

    publishScoreboard();
}


// ============================================================
// Iterate
// ============================================================

bool InspectionScorer::Iterate()
{
    AppCastingMOOSApp::Iterate();
    publishScoreboard();
    return true;
}


// ============================================================
// Coverage tracking
// ============================================================

void InspectionScorer::updateCoverage(const string& team,
                                       double vx, double vy)
{
    TeamState& ts = _teams[team];

    for (auto& kv : _samples) {
        const string& label        = kv.first;
        const auto&   samplePts    = kv.second;
        auto& coveredSet           = ts.covered[label];

        for (size_t i = 0; i < samplePts.size(); ++i) {
            if (coveredSet.count(i)) continue;   // already covered
            double dx = samplePts[i].x - vx;
            double dy = samplePts[i].y - vy;
            if (sqrt(dx*dx + dy*dy) <= _coverageRadius)
                coveredSet.insert(i);
        }
    }
}


// ============================================================
// Score computation
// ============================================================

int InspectionScorer::computeTeamScore(const TeamState& ts) const
{
    double score = 0.0;

    // Coverage score
    size_t totalSamples = 0, coveredSamples = 0;
    for (auto& kv : _samples) {
        totalSamples += kv.second.size();
        auto it = ts.covered.find(kv.first);
        if (it != ts.covered.end())
            coveredSamples += it->second.size();
    }
    if (totalSamples > 0) {
        double frac = static_cast<double>(coveredSamples) / totalSamples;
        double coverageEarned = min(1.0, frac / _coverageThreshold) * _coverageScore;
        score += coverageEarned;
    }

    // Anomaly score
    for (auto& kv : ts.anomalyClaimed)
        if (kv.second) score += _anomalyScore;

    // False alarm penalty
    score -= ts.falseAlarms * _falseAlarmPenalty;

    return static_cast<int>(max(0.0, score));
}

void InspectionScorer::publishScoreboard()
{
    // Format: "team=alpha,score=1420,coverage=0.72,anomalies=2,fa=1|team=bravo,..."
    ostringstream ss;
    bool first = true;
    for (auto& kv : _teams) {
        const TeamState& ts = kv.second;

        size_t totalSamples = 0, coveredSamples = 0;
        for (auto& sv : _samples) {
            totalSamples += sv.second.size();
            auto it = ts.covered.find(sv.first);
            if (it != ts.covered.end())
                coveredSamples += it->second.size();
        }
        double frac = totalSamples ? (double)coveredSamples / totalSamples : 0.0;

        int confirmed = 0;
        for (auto& cv : ts.anomalyClaimed)
            if (cv.second) confirmed++;

        if (!first) ss << "|";
        ss << fixed << setprecision(3);
        ss << "team="      << ts.name
           << ",score="    << computeTeamScore(ts)
           << ",coverage=" << frac
           << ",anomalies="<< confirmed
           << ",fa="       << ts.falseAlarms;
        first = false;
    }
    Notify("INSPECTION_SCORE", ss.str());
}


// ============================================================
// AppCast
// ============================================================

bool InspectionScorer::buildReport()
{
    m_msgs << "  Pipelines:  " << _pipelines.size() << "\n";
    m_msgs << "  Anomalies:  " << _anomalies.size() << "\n";

    size_t totalSamplesAll = 0;
    for (auto& kv : _samples) totalSamplesAll += kv.second.size();
    m_msgs << "  Grid pts:   " << totalSamplesAll << " (step=" << _sampleStep << "m)\n";
    m_msgs << "\n";

    m_msgs << left << setw(10) << "Team"
           << setw(8)  << "Score"
           << setw(10) << "Coverage"
           << setw(10) << "Anomalies"
           << setw(6)  << "FAs"
           << "\n";
    m_msgs << string(44, '-') << "\n";

    for (auto& kv : _teams) {
        const TeamState& ts = kv.second;

        size_t total = 0, covered = 0;
        for (auto& sv : _samples) {
            total += sv.second.size();
            auto it = ts.covered.find(sv.first);
            if (it != ts.covered.end())
                covered += it->second.size();
        }
        double frac = total ? (double)covered / total : 0.0;

        int confirmed = 0;
        for (auto& cv : ts.anomalyClaimed)
            if (cv.second) confirmed++;

        m_msgs << left << setw(10) << ts.name
               << setw(8)  << computeTeamScore(ts)
               << setw(10) << (to_string((int)(frac*100)) + "%")
               << setw(10) << (to_string(confirmed) + "/" + to_string(_anomalies.size()))
               << setw(6)  << ts.falseAlarms
               << "\n";
    }

    return true;
}


// ============================================================
// Config parsers (mirrors pInfrastructureSensor)
// ============================================================

bool InspectionScorer::parsePipelineSpec(const string& spec)
{
    Pipeline p;
    p.label = getField(spec, "label");
    p.depth = atof(getField(spec, "depth").c_str());

    if (p.label.empty()) {
        reportConfigWarning("pipeline= missing 'label': " + spec);
        return false;
    }

    string pts_str = getField(spec, "points");
    istringstream ss(pts_str);
    string seg;
    while (getline(ss, seg, ':')) {
        istringstream sv(seg);
        string sx, sy;
        if (getline(sv, sx, ',') && getline(sv, sy))
            p.points.emplace_back(atof(sx.c_str()), atof(sy.c_str()));
    }
    if (p.points.size() < 2) {
        reportConfigWarning("pipeline '" + p.label + "' has fewer than 2 points.");
        return false;
    }
    _pipelines.push_back(p);
    return true;
}

bool InspectionScorer::parseAnomalySpec(const string& spec)
{
    Anomaly a;
    a.pipeline_label = getField(spec, "pipeline");
    a.x    = atof(getField(spec, "x").c_str());
    a.y    = atof(getField(spec, "y").c_str());
    a.type = getField(spec, "type");

    if (a.pipeline_label.empty()) {
        reportConfigWarning("anomaly= missing 'pipeline': " + spec);
        return false;
    }
    _anomalies.push_back(a);
    return true;
}

void InspectionScorer::buildSampleGrid()
{
    for (const Pipeline& p : _pipelines) {
        vector<SamplePoint>& pts = _samples[p.label];
        for (size_t i = 0; i + 1 < p.points.size(); ++i) {
            double ax = p.points[i].first,   ay = p.points[i].second;
            double bx = p.points[i+1].first, by = p.points[i+1].second;
            double segLen = sqrt(pow(bx-ax,2) + pow(by-ay,2));
            int nSteps = max(1, (int)(segLen / _sampleStep));
            for (int s = 0; s <= nSteps; ++s) {
                double t = (double)s / nSteps;
                SamplePoint sp;
                sp.x = ax + t*(bx-ax);
                sp.y = ay + t*(by-ay);
                pts.push_back(sp);
            }
        }
    }
}


// ============================================================
// String helpers
// ============================================================

string InspectionScorer::getField(const string& str, const string& key) const
{
    string search = key + "=";
    // Try as-is then case-insensitive
    size_t pos = str.find(search);
    if (pos == string::npos) {
        string ls = str, lk = search;
        for (char& c : ls) c = (char)tolower(c);
        for (char& c : lk) c = (char)tolower(c);
        pos = ls.find(lk);
        if (pos == string::npos) return "";
    }
    size_t start = pos + search.size();
    size_t end   = str.find(',', start);
    if (end == string::npos) end = str.size();
    return str.substr(start, end - start);
}

string InspectionScorer::toUpper(const string& s) const
{
    string r = s;
    for (char& c : r) c = (char)toupper(c);
    return r;
}

string InspectionScorer::toLower(const string& s) const
{
    string r = s;
    for (char& c : r) c = (char)tolower(c);
    return r;
}
