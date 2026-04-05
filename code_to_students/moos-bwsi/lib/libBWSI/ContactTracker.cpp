/************************************************************/
/*    FILE: ContactTracker.cpp                              */
/*    ORGN: BWSI AUVC                                       */
/************************************************************/
#include "ContactTracker.h"

ContactTracker::ContactTracker() : _emptyCount(0) {}

bool ContactTracker::processReport(const std::string& rawReport) {
  NodeReport r = NodeReport::fromString(rawReport);
  if (!r.valid())
    return false;

  for (NodeReport& c : _contacts) {
    if (c.sameContact(r)) {
      c = r;  // update in place
      return true;
    }
  }
  _contacts.push_back(r);
  return true;
}

void ContactTracker::markCollected(const NodeReport& contact) {
  for (const NodeReport& c : _collected) {
    if (c.sameContact(contact))
      return;  // already marked
  }
  _collected.push_back(contact);
}

bool ContactTracker::isCollected(const NodeReport& contact) const {
  for (const NodeReport& c : _collected) {
    if (c.sameContact(contact))
      return true;
  }
  return false;
}

int ContactTracker::tickEmpty() {
  return ++_emptyCount;
}

void ContactTracker::tickReceived() {
  _emptyCount = 0;
}
