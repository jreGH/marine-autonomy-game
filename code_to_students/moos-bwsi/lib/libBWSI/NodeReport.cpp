/************************************************************/
/*    FILE: NodeReport.cpp                                  */
/*    ORGN: BWSI AUVC                                       */
/************************************************************/
#include "NodeReport.h"

NodeReport NodeReport::fromString(const std::string& s) {
  NodeReport r;
  std::string key, val;
  std::istringstream iss(s);
  // The NODE_REPORT format is KEY=VALUE,KEY=VALUE,...
  // getline with '=' reads the key; the nested getline with ',' reads the value.
  // The last pair has no trailing comma, which getline handles correctly (reads to EOF).
  while (std::getline(std::getline(iss, key, '=') >> std::ws, val, ',')) {
    if (!key.empty())
      r._fields[key] = val;
  }
  return r;
}

std::string NodeReport::getString(const std::string& key,
                                   const std::string& def) const {
  auto it = _fields.find(key);
  return (it != _fields.end()) ? it->second : def;
}

double NodeReport::getDouble(const std::string& key, double def) const {
  auto it = _fields.find(key);
  if (it == _fields.end() || it->second.empty())
    return def;
  try {
    return std::stod(it->second);
  } catch (const std::exception&) {
    return def;
  }
}

bool NodeReport::hasField(const std::string& key) const {
  return _fields.count(key) > 0;
}

bool NodeReport::sameContact(const NodeReport& other) const {
  return name() == other.name() && type() == other.type();
}

double NodeReport::distanceTo2D(double ox, double oy) const {
  double dx = x() - ox;
  double dy = y() - oy;
  return std::sqrt(dx * dx + dy * dy);
}

double NodeReport::rangeTo3D(double ox, double oy, double od) const {
  double dx = x() - ox;
  double dy = y() - oy;
  double dz = depth() - od;
  return std::sqrt(dx * dx + dy * dy + dz * dz);
}
