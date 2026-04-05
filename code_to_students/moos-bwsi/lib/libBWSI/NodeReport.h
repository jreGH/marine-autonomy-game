/************************************************************/
/*    FILE: NodeReport.h                                    */
/*    ORGN: BWSI AUVC                                       */
/*                                                          */
/*    Represents a parsed MOOS NODE_REPORT message.         */
/*    Format: KEY=VALUE,KEY=VALUE,...                        */
/*    Standard fields: NAME, TYPE, GROUP, X, Y, DEP,        */
/*                     HDG, SPD, LAT, LON                   */
/************************************************************/
#pragma once

#include <cmath>
#include <map>
#include <sstream>
#include <string>

class NodeReport {
public:
  // Parse from a raw NODE_REPORT string.
  // Returns an empty (invalid) report if the string is malformed.
  static NodeReport fromString(const std::string& s);

  // Named accessors with safe defaults (empty string / 0.0).
  std::string name()    const { return getString("NAME"); }
  std::string type()    const { return getString("TYPE"); }
  std::string group()   const { return getString("GROUP"); }
  double      x()       const { return getDouble("X"); }
  double      y()       const { return getDouble("Y"); }
  double      depth()   const { return getDouble("DEP"); }
  double      heading() const { return getDouble("HDG"); }
  double      speed()   const { return getDouble("SPD"); }

  // Generic field access. Returns def if the key is missing or unparseable.
  std::string getString(const std::string& key,
                        const std::string& def = "") const;
  double      getDouble(const std::string& key,
                        double def = 0.0)             const;
  bool        hasField (const std::string& key)       const;

  // Two reports refer to the same physical contact when NAME and TYPE match.
  bool sameContact(const NodeReport& other) const;

  // 2-D Euclidean distance from this contact to the given point.
  double distanceTo2D(double ox, double oy) const;

  // 3-D slant range from this contact to the given point (includes depth).
  double rangeTo3D(double ox, double oy, double odepth) const;

  // A report is valid when it has at least a NAME and a TYPE field.
  bool valid() const { return !name().empty() && !type().empty(); }
  bool empty() const { return _fields.empty(); }

private:
  std::map<std::string, std::string> _fields;
};
