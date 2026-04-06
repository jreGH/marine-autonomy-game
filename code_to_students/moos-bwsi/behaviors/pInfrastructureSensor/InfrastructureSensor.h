/************************************************************/
/*    FILE: InfrastructureSensor.h                          */
/*    ORGN: BWSI AUVC                                       */
/*                                                          */
/*    Shoreside app that simulates a forward-looking        */
/*    pipeline / cable detection sonar on each vehicle.     */
/*                                                          */
/*    The app knows the ground-truth geometry of one or     */
/*    more undersea infrastructure polylines (pipelines,    */
/*    cables) and anomaly positions along them.  Each       */
/*    iteration it checks every known vehicle against the   */
/*    geometry and, when the sensor model fires, posts a    */
/*    detection report that is bridged to that vehicle's    */
/*    MOOS community.                                       */
/*                                                          */
/*  Config (in shoreside.moos):                             */
/*    pipeline = label=cable_01,depth=30.0,                 */
/*               points=-300,-100:-200,-150:-100,-200       */
/*    anomaly  = pipeline=cable_01,x=-100,y=-200,           */
/*               type=damage                                */
/*    detect_range  = 30.0   // sensor radius (m)           */
/*    detect_cone   = 60.0   // half-angle forward cone (°) */
/*    noise_sigma   = 3.0    // position noise (m)          */
/*    p_false_alarm = 0.02   // false alarms per veh/s      */
/*    reveal_pipe   = false  // show pipe in viewer on hit  */
/*                                                          */
/*  Publishes (shoreside, bridged to each vehicle):         */
/*    INFRASTRUCTURE_DETECT_<VNAME>                         */
/*      pipeline=<label>,x=<f>,y=<f>,depth=<f>,            */
/*      type=<pipe|anomaly|false_alarm>,range=<f>,          */
/*      confidence=<f>[,anomaly_type=<s>]                   */
/*    confidence is the P_D value (0–1) used for this       */
/*    detection — use it to weight Bayesian belief updates. */
/*  Publishes (shoreside viewer only):                      */
/*    VIEW_SEGLIST  — pipeline outline when reveal_pipe=true */
/*    VIEW_POINT    — anomaly marker when anomaly found     */
/************************************************************/
#pragma once

#include "MOOS/libMOOS/MOOSLib.h"
#include "MOOS/libMOOS/Thirdparty/AppCasting/AppCastingMOOSApp.h"

#include <map>
#include <random>
#include <string>
#include <utility>
#include <vector>

class InfrastructureSensor : public AppCastingMOOSApp {
public:
    InfrastructureSensor();
    ~InfrastructureSensor() {}

protected:
    bool OnNewMail(MOOSMSG_LIST& NewMail);
    bool Iterate();
    bool OnConnectToServer();
    bool OnStartUp();
    bool buildReport();

    void RegisterVariables();

private:
    // ----------------------------------------------------------------
    // Data structures
    // ----------------------------------------------------------------

    struct Pipeline {
        std::string              label;
        double                   depth;      // metres, positive downward
        std::vector<std::pair<double,double>> points;  // (x, y) in local metres
    };

    struct Anomaly {
        std::string pipeline_label;
        double      x, y;           // local metres
        std::string type;           // e.g. "damage", "corrosion", "obstruction"
        bool        revealed;       // true once any vehicle has detected it
    };

    struct VehicleRecord {
        std::string name;
        double x, y, depth, heading, speed;
        double time_updated;
    };

    // ----------------------------------------------------------------
    // Configuration
    // ----------------------------------------------------------------
    double _detectRange;     // maximum sensor range (m)
    double _detectCone;      // half-angle of forward detection cone (deg)
    double _noiseSigma;      // std-dev of position noise on detections (m)
    double _pFalseAlarm;     // false alarm rate per vehicle per second
    double _detectInterval;  // minimum seconds between reports for same (veh,pipe)
    bool   _revealPipe;      // progressively show pipeline in pMarineViewer

    // ----------------------------------------------------------------
    // Mission state
    // ----------------------------------------------------------------
    std::vector<Pipeline>         _pipelines;
    std::vector<Anomaly>          _anomalies;
    std::map<std::string, VehicleRecord> _vehicles;

    // Rate limiting: (vehicle_name, pipeline_label) → last detection time
    std::map<std::pair<std::string,std::string>, double> _lastDetect;

    // Track which pipelines have been partially revealed in the viewer
    std::map<std::string, bool> _pipeRevealed;

    // Anomaly detection: vehicle_name → set of anomaly indices already reported
    std::map<std::string, std::vector<size_t>> _anomaliesReported;

    // Detection counters for the appcast report
    int _totalDetections;
    int _totalFalseAlarms;
    int _totalAnomalyDetections;

    // RNG
    std::mt19937                          _rng;
    std::uniform_real_distribution<double> _uniform;
    std::normal_distribution<double>       _gauss;

    // ----------------------------------------------------------------
    // Private helpers
    // ----------------------------------------------------------------

    // Parse a "label=...,depth=...,points=x,y:x,y:..." config string
    bool parsePipelineSpec(const std::string& spec);
    // Parse a "pipeline=...,x=...,y=...,type=..." config string
    bool parseAnomalySpec(const std::string& spec);

    // Find the closest point on segment (ax,ay)–(bx,by) to (vx,vy).
    // Returns the closest (cx,cy) and sets dist_out.
    std::pair<double,double> closestPointOnSegment(
        double vx, double vy,
        double ax, double ay,
        double bx, double by,
        double& dist_out) const;

    // Compass bearing (deg, 0=north, clockwise) from (fx,fy) to (tx,ty).
    double bearingDeg(double fx, double fy, double tx, double ty) const;

    // Shortest angular difference in (-180, 180].
    double angleDiff(double a, double b) const;

    // True when the point (px,py) is within _detectCone of the vehicle heading.
    bool inDetectionCone(const VehicleRecord& v, double px, double py) const;

    // True when the vehicle is close enough in depth to use the sensor
    // against a pipeline at pipeline_depth.
    bool depthGate(const VehicleRecord& v, double pipeline_depth) const;

    // Build and publish one detection message to shoreside for bridging.
    // confidence: the P_D value used for this detection (0–1), included
    //             in the published message so students can weight observations.
    void publishDetection(const std::string& vname,
                          const std::string& pipeline_label,
                          double raw_x, double raw_y, double depth,
                          const std::string& type,
                          const std::string& anomaly_type,
                          double range,
                          double confidence);

    // Build VIEW_SEGLIST spec for a pipeline (for pMarineViewer).
    std::string pipelineViewSeglist(const Pipeline& p) const;

    // Extract a named field from a comma-separated KEY=VALUE string.
    std::string getField(const std::string& str, const std::string& key) const;
};
