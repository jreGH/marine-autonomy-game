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
#include <cmath>
#include <map>
#include <string>
#include <utility>
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

  // --- Uncertainty helpers ---

  // Seconds elapsed since the last NODE_REPORT was received for this contact.
  // Returns -1 if the contact name is not known.
  double contactAge(const std::string& name) const;

  // Exponential-decay confidence in [0, 1].
  //   confidence = exp( -age * ln2 / half_life )
  // Returns 0 when the contact is unknown.
  // half_life: seconds at which confidence falls to 0.5 (default 10 s).
  double contactConfidence(const std::string& name,
                           double half_life = 10.0) const;

  // Dead-reckoning position estimate dt seconds into the future (or past
  // if dt is negative), assuming constant heading and speed from the last
  // report.  Returns {NaN, NaN} if the contact is unknown.
  std::pair<double, double> predictPosition(const std::string& name,
                                            double dt) const;

private:
  std::vector<NodeReport>      _contacts;
  std::vector<NodeReport>      _collected;
  std::map<std::string, double> _lastSeenTime; // contact name → MOOSTime
  int _emptyCount;
};
