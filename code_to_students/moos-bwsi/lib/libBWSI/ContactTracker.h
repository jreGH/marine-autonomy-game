/************************************************************/
/*    FILE: ContactTracker.h                                */
/*    ORGN: BWSI AUVC                                       */
/*                                                          */
/*    Manages a live list of known contacts and a separate  */
/*    set of already-handled contacts.  Replaces the        */
/*    manual _contactList / _contactsCollected pattern      */
/*    that was duplicated across every pChallenge_* app.    */
/************************************************************/
#pragma once

#include "NodeReport.h"
#include <string>
#include <vector>

class ContactTracker {
public:
  ContactTracker();

  // Parse a raw NODE_REPORT string and update the contact list.
  // If a contact with the same NAME+TYPE already exists it is replaced;
  // otherwise a new entry is added.
  // Returns false when the report is malformed (missing NAME or TYPE).
  bool processReport(const std::string& rawReport);

  // All currently known contacts (most-recent state per unique NAME+TYPE).
  const std::vector<NodeReport>& contacts() const { return _contacts; }

  // Mark a contact as already handled (tagged, bitten, photographed, …).
  // Idempotent: calling it twice for the same contact is harmless.
  void markCollected(const NodeReport& contact);

  // Returns true when this contact has previously been marked collected.
  bool isCollected(const NodeReport& contact) const;

  // Call once per Iterate() when the mail queue was empty.
  // Increments and returns the empty-iteration counter.
  int tickEmpty();

  // Call once per Iterate() when at least one report was processed.
  // Resets the empty-iteration counter to zero.
  void tickReceived();

  int emptyCount() const { return _emptyCount; }

private:
  std::vector<NodeReport> _contacts;
  std::vector<NodeReport> _collected;
  int _emptyCount;
};
