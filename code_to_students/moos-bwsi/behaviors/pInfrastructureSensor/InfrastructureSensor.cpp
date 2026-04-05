/************************************************************/
/*    FILE: InfrastructureSensor.cpp                        */
/*    ORGN: BWSI AUVC                                       */
/************************************************************/

#include "InfrastructureSensor.h"
#include "MBUtils.h"      // tolower(), strContains(), …  (MOOS-IvP utility)

#include <cmath>
#include <ctime>
#include <sstream>
#include <iomanip>

using namespace std;

// ============================================================
// Constructor
// ============================================================

InfrastructureSensor::InfrastructureSensor()
    : _detectRange(30.0),
      _detectCone(60.0),
      _noiseSigma(3.0),
      _pFalseAlarm(0.02),
      _detectInterval(0.5),
      _revealPipe(false),
      _totalDetections(0),
      _totalFalseAlarms(0),
      _totalAnomalyDetections(0),
      _rng(static_cast<unsigned>(time(nullptr))),
      _uniform(0.0, 1.0),
      _gauss(0.0, 1.0)
{}


// ============================================================
// MOOS lifecycle
// ============================================================

bool InfrastructureSensor::OnConnectToServer()
{
    RegisterVariables();
    return true;
}

bool InfrastructureSensor::OnStartUp()
{
    AppCastingMOOSApp::OnStartUp();

    STRING_LIST sParams;
    m_MissionReader.EnableVerbatimQuoting(false);
    if (!m_MissionReader.GetConfiguration(GetAppName(), sParams))
        reportConfigWarning("No config block found for " + GetAppName());

    for (auto& line : sParams) {
        string param = tolower(biteStringX(line, '='));
        string val   = line;                     // everything after first '='

        if      (param == "pipeline")
            parsePipelineSpec(val);
        else if (param == "anomaly")
            parseAnomalySpec(val);
        else if (param == "detect_range")
            _detectRange = atof(val.c_str());
        else if (param == "detect_cone")
            _detectCone  = atof(val.c_str());
        else if (param == "noise_sigma")
            _noiseSigma  = atof(val.c_str());
        else if (param == "p_false_alarm")
            _pFalseAlarm = atof(val.c_str());
        else if (param == "detect_interval")
            _detectInterval = atof(val.c_str());
        else if (param == "reveal_pipe")
            _revealPipe = (tolower(val) == "true");
        else
            reportUnhandledConfigWarning(param);
    }

    if (_pipelines.empty())
        reportConfigWarning("No pipeline= entries found — sensor will do nothing.");

    // Publish pipeline geometry to pMarineViewer immediately so the
    // shoreside instructor sees the full layout from the start.
    // (reveal_pipe controls whether the vehicle-side viewers see this.)
    for (const Pipeline& p : _pipelines)
        Notify("VIEW_SEGLIST", pipelineViewSeglist(p));

    RegisterVariables();
    return true;
}

void InfrastructureSensor::RegisterVariables()
{
    AppCastingMOOSApp::RegisterVariables();
    Register("NODE_REPORT", 0);
}


// ============================================================
// Mail handling
// ============================================================

bool InfrastructureSensor::OnNewMail(MOOSMSG_LIST& NewMail)
{
    AppCastingMOOSApp::OnNewMail(NewMail);

    for (auto& msg : NewMail) {
        if (msg.GetKey() != "NODE_REPORT")
            continue;

        string raw = msg.GetString();

        // Parse the essential fields from NAME=...,X=...,Y=...,DEP=...,HDG=...
        VehicleRecord rec;
        rec.name         = getField(raw, "NAME");
        rec.x            = atof(getField(raw, "X").c_str());
        rec.y            = atof(getField(raw, "Y").c_str());
        rec.depth        = atof(getField(raw, "DEP").c_str());
        rec.heading      = atof(getField(raw, "HDG").c_str());
        rec.speed        = atof(getField(raw, "SPD").c_str());
        rec.time_updated = MOOSTime();

        if (!rec.name.empty())
            _vehicles[rec.name] = rec;
    }
    return true;
}


// ============================================================
// Iterate — sensor simulation runs here
// ============================================================

bool InfrastructureSensor::Iterate()
{
    AppCastingMOOSApp::Iterate();

    double now = MOOSTime();
    double dt  = 1.0 / GetAppFreq();   // seconds per iteration

    for (auto& kv : _vehicles) {
        const VehicleRecord& v = kv.second;

        // Skip stale vehicle records (not heard from in 5 s)
        if (now - v.time_updated > 5.0)
            continue;

        // ---- Pipeline segment detections ----
        for (const Pipeline& pipe : _pipelines) {
            // Rate limit: one detection per (vehicle, pipeline) per interval
            auto key = make_pair(v.name, pipe.label);
            auto it  = _lastDetect.find(key);
            if (it != _lastDetect.end() &&
                now - it->second < _detectInterval)
                continue;

            // Depth gate: vehicle must be within 20 m of pipeline depth
            if (!depthGate(v, pipe.depth))
                continue;

            // Find the closest point across all segments
            double   bestDist = 1e9;
            double   bestX = 0, bestY = 0;
            bool     found = false;

            for (size_t i = 0; i + 1 < pipe.points.size(); ++i) {
                double ax = pipe.points[i].first,   ay = pipe.points[i].second;
                double bx = pipe.points[i+1].first, by = pipe.points[i+1].second;

                double dist;
                auto cp = closestPointOnSegment(v.x, v.y, ax, ay, bx, by, dist);

                if (dist < bestDist) {
                    bestDist = dist;
                    bestX    = cp.first;
                    bestY    = cp.second;
                    found    = true;
                }
            }

            if (!found || bestDist > _detectRange)
                continue;

            // Must be within the forward detection cone
            if (!inDetectionCone(v, bestX, bestY))
                continue;

            // Stochastic detection: P_D falls linearly with range
            double pd = 1.0 - (bestDist / _detectRange);
            if (_uniform(_rng) > pd)
                continue;

            // Detected — publish with position noise
            publishDetection(v.name, pipe.label,
                             bestX, bestY, pipe.depth,
                             "pipe", "",
                             bestDist);
            _lastDetect[key] = now;
            _totalDetections++;

            // Optionally reveal the pipeline in pMarineViewer
            if (_revealPipe && !_pipeRevealed[pipe.label]) {
                Notify("VIEW_SEGLIST", pipelineViewSeglist(pipe));
                _pipeRevealed[pipe.label] = true;
            }
        }

        // ---- Anomaly detections ----
        for (size_t ai = 0; ai < _anomalies.size(); ++ai) {
            Anomaly& anom = _anomalies[ai];

            // Already reported to this vehicle?
            auto& reported = _anomaliesReported[v.name];
            bool already   = false;
            for (size_t idx : reported)
                if (idx == ai) { already = true; break; }
            if (already)
                continue;

            // Check depth gate against the pipeline this anomaly belongs to
            double anomalyDepth = 0.0;
            for (const Pipeline& p : _pipelines) {
                if (p.label == anom.pipeline_label) {
                    anomalyDepth = p.depth;
                    break;
                }
            }
            if (!depthGate(v, anomalyDepth))
                continue;

            double dx = anom.x - v.x;
            double dy = anom.y - v.y;
            double dist = sqrt(dx*dx + dy*dy);

            if (dist > _detectRange)
                continue;
            if (!inDetectionCone(v, anom.x, anom.y))
                continue;

            // Higher P_D for anomalies (they are prominent features)
            double pd = 1.0 - 0.5 * (dist / _detectRange);
            if (_uniform(_rng) > pd)
                continue;

            publishDetection(v.name, anom.pipeline_label,
                             anom.x, anom.y, anomalyDepth,
                             "anomaly", anom.type,
                             dist);
            reported.push_back(ai);
            _totalAnomalyDetections++;

            if (!anom.revealed) {
                anom.revealed = true;
                // Post a marker in pMarineViewer
                ostringstream pt;
                pt << "x=" << anom.x << ",y=" << anom.y
                   << ",label=" << anom.pipeline_label << "_" << anom.type
                   << ",color=yellow,vertex_size=8";
                Notify("VIEW_POINT", pt.str());
            }
        }

        // ---- False alarms ----
        // Rate: _pFalseAlarm false alarms per vehicle per second
        double fa_prob = _pFalseAlarm * dt;
        if (_uniform(_rng) < fa_prob && !_pipelines.empty()) {
            // Pick a random pipeline and a random point along it
            size_t pi = static_cast<size_t>(_uniform(_rng) * _pipelines.size())
                        % _pipelines.size();
            const Pipeline& pipe = _pipelines[pi];
            if (!pipe.points.empty()) {
                size_t pi2 = static_cast<size_t>(_uniform(_rng) * pipe.points.size())
                             % pipe.points.size();
                double fx = pipe.points[pi2].first  + _gauss(_rng) * _detectRange * 0.5;
                double fy = pipe.points[pi2].second + _gauss(_rng) * _detectRange * 0.5;
                double fd = sqrt(pow(fx - v.x, 2) + pow(fy - v.y, 2));
                publishDetection(v.name, pipe.label,
                                 fx, fy, pipe.depth,
                                 "false_alarm", "",
                                 fd);
                _totalFalseAlarms++;
            }
        }
    }

    return true;
}


// ============================================================
// AppCast report
// ============================================================

bool InfrastructureSensor::buildReport()
{
    m_msgs << "  Pipelines:          " << _pipelines.size()  << "\n";
    m_msgs << "  Anomalies:          " << _anomalies.size()  << "\n";
    m_msgs << "  Known vehicles:     " << _vehicles.size()   << "\n";
    m_msgs << "\n";
    m_msgs << "  Sensor params:\n";
    m_msgs << "    detect_range    = " << _detectRange     << " m\n";
    m_msgs << "    detect_cone     = " << _detectCone      << " deg\n";
    m_msgs << "    noise_sigma     = " << _noiseSigma      << " m\n";
    m_msgs << "    p_false_alarm   = " << _pFalseAlarm     << " /veh/s\n";
    m_msgs << "    reveal_pipe     = " << (_revealPipe ? "true" : "false") << "\n";
    m_msgs << "\n";
    m_msgs << "  Detections (pipe):  " << _totalDetections       << "\n";
    m_msgs << "  Detections (anom):  " << _totalAnomalyDetections << "\n";
    m_msgs << "  False alarms:       " << _totalFalseAlarms       << "\n";
    m_msgs << "\n";

    // Per-pipeline anomaly discovery table
    m_msgs << "  Anomaly status:\n";
    for (size_t i = 0; i < _anomalies.size(); ++i) {
        const Anomaly& a = _anomalies[i];
        m_msgs << "    [" << (a.revealed ? "FOUND" : "     ") << "] "
               << a.pipeline_label << "  " << a.type
               << "  (" << a.x << ", " << a.y << ")\n";
    }

    return true;
}


// ============================================================
// Config parsers
// ============================================================

bool InfrastructureSensor::parsePipelineSpec(const string& spec)
{
    // Expected format:
    //   label=cable_01,depth=30.0,points=-300,-100:-200,-150:-100,-200

    Pipeline p;
    p.label = getField(spec, "label");
    p.depth = atof(getField(spec, "depth").c_str());

    if (p.label.empty()) {
        reportConfigWarning("pipeline= spec missing 'label' field: " + spec);
        return false;
    }

    string pts_str = getField(spec, "points");
    if (pts_str.empty()) {
        reportConfigWarning("pipeline= spec missing 'points' field: " + spec);
        return false;
    }

    // points field: x1,y1:x2,y2:...
    istringstream ss(pts_str);
    string segment;
    while (getline(ss, segment, ':')) {
        istringstream sv(segment);
        string sx, sy;
        if (getline(sv, sx, ',') && getline(sv, sy)) {
            double x = atof(sx.c_str());
            double y = atof(sy.c_str());
            p.points.emplace_back(x, y);
        }
    }

    if (p.points.size() < 2) {
        reportConfigWarning("pipeline '" + p.label + "' has fewer than 2 points.");
        return false;
    }

    _pipelines.push_back(p);
    return true;
}

bool InfrastructureSensor::parseAnomalySpec(const string& spec)
{
    // Expected format:
    //   pipeline=cable_01,x=-100.0,y=-200.0,type=damage

    Anomaly a;
    a.pipeline_label = getField(spec, "pipeline");
    a.x              = atof(getField(spec, "x").c_str());
    a.y              = atof(getField(spec, "y").c_str());
    a.type           = getField(spec, "type");
    a.revealed       = false;

    if (a.pipeline_label.empty() || a.type.empty()) {
        reportConfigWarning("anomaly= spec missing 'pipeline' or 'type': " + spec);
        return false;
    }

    _anomalies.push_back(a);
    return true;
}


// ============================================================
// Geometry helpers
// ============================================================

pair<double,double> InfrastructureSensor::closestPointOnSegment(
    double vx, double vy,
    double ax, double ay,
    double bx, double by,
    double& dist_out) const
{
    double dx = bx - ax, dy = by - ay;
    double len2 = dx*dx + dy*dy;

    if (len2 < 1e-12) {
        // Degenerate segment (zero length) — return the endpoint
        dist_out = sqrt((vx-ax)*(vx-ax) + (vy-ay)*(vy-ay));
        return {ax, ay};
    }

    // t is the parameter in [0,1] of the closest point on the segment
    double t = ((vx - ax)*dx + (vy - ay)*dy) / len2;
    t = max(0.0, min(1.0, t));

    double cx = ax + t*dx;
    double cy = ay + t*dy;
    dist_out = sqrt((vx-cx)*(vx-cx) + (vy-cy)*(vy-cy));
    return {cx, cy};
}

double InfrastructureSensor::bearingDeg(
    double fx, double fy, double tx, double ty) const
{
    // In MOOS local XY: x increases east, y increases north.
    // Bearing 0 = north, increases clockwise.
    double dx = tx - fx;
    double dy = ty - fy;
    double bearing = atan2(dx, dy) * 180.0 / M_PI;
    if (bearing < 0.0) bearing += 360.0;
    return bearing;
}

double InfrastructureSensor::angleDiff(double a, double b) const
{
    double diff = fmod(a - b + 540.0, 360.0) - 180.0;
    return diff;
}

bool InfrastructureSensor::inDetectionCone(
    const VehicleRecord& v, double px, double py) const
{
    double bearing = bearingDeg(v.x, v.y, px, py);
    double diff    = fabs(angleDiff(bearing, v.heading));
    return diff <= _detectCone;
}

bool InfrastructureSensor::depthGate(
    const VehicleRecord& v, double pipeline_depth) const
{
    // Vehicle must be within 20 m depth of the pipeline to use sensor.
    return fabs(v.depth - pipeline_depth) <= 20.0;
}


// ============================================================
// Detection publisher
// ============================================================

void InfrastructureSensor::publishDetection(
    const string& vname,
    const string& pipeline_label,
    double raw_x, double raw_y, double depth,
    const string& type,
    const string& anomaly_type,
    double range)
{
    // Add Gaussian position noise
    double nx = raw_x + _gauss(_rng) * _noiseSigma;
    double ny = raw_y + _gauss(_rng) * _noiseSigma;

    ostringstream msg;
    msg << fixed << setprecision(2);
    msg << "pipeline="    << pipeline_label
        << ",x="          << nx
        << ",y="          << ny
        << ",depth="      << depth
        << ",type="       << type
        << ",range="      << range;

    if (!anomaly_type.empty())
        msg << ",anomaly_type=" << anomaly_type;

    // Variable name: INFRASTRUCTURE_DETECT_<VEHICLE_NAME_UPPER>
    string vname_upper = vname;
    for (char& c : vname_upper) c = static_cast<char>(toupper(c));

    Notify("INFRASTRUCTURE_DETECT_" + vname_upper, msg.str());
}


// ============================================================
// Viewer helpers
// ============================================================

string InfrastructureSensor::pipelineViewSeglist(const Pipeline& p) const
{
    // VIEW_SEGLIST format: pts=x1,y1:x2,y2:...,label=...,edge_color=...,edge_size=...
    ostringstream ss;
    ss << "pts=";
    for (size_t i = 0; i < p.points.size(); ++i) {
        if (i > 0) ss << ":";
        ss << fixed << setprecision(1)
           << p.points[i].first << "," << p.points[i].second;
    }
    ss << ",label=" << p.label
       << ",edge_color=yellow,edge_size=2,vertex_color=yellow,vertex_size=4";
    return ss.str();
}


// ============================================================
// Field extractor — parse KEY=VALUE from comma-delimited string
// ============================================================

string InfrastructureSensor::getField(
    const string& str, const string& key) const
{
    // Handles:  ...,key=value,...   where value may itself contain '='
    // but not commas (the next comma ends the value).
    string search = key + "=";
    size_t pos = str.find(search);
    if (pos == string::npos) {
        // Try case-insensitive by lower-casing both
        string ls = str, lk = search;
        for (char& c : ls) c = static_cast<char>(tolower(c));
        for (char& c : lk) c = static_cast<char>(tolower(c));
        pos = ls.find(lk);
        if (pos == string::npos) return "";
    }
    size_t start = pos + search.size();
    size_t end   = str.find(',', start);
    if (end == string::npos) end = str.size();
    return str.substr(start, end - start);
}
