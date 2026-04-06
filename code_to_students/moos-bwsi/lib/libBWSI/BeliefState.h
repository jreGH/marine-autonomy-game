/************************************************************/
/*    FILE: BeliefState.h                                   */
/*    ORGN: BWSI AUVC                                       */
/*                                                          */
/*    Bayesian log-odds belief tracker for binary           */
/*    hypotheses (feature present vs. absent).              */
/*                                                          */
/*    Uses the log-odds form:                               */
/*      L = log( P(present) / P(absent) )                  */
/*    which converts Bayesian products into sums and        */
/*    avoids numerical underflow.                           */
/*                                                          */
/*    Update rule:                                          */
/*      positive: L += log( P_D / P_FA )                   */
/*      negative: L -= log( (1-P_D) / (1-P_FA) )          */
/************************************************************/
#pragma once

#include <cmath>

class BeliefState {
public:
  // Construct with optional initial log-odds (default = 0.0 → 50% prior).
  explicit BeliefState(double initialLogOdds = 0.0);

  // --- Update methods ---

  // Call when the sensor fires on this candidate (positive detection).
  // pd  = probability of detection given feature is present  (0 < pd  < 1)
  // pfa = probability of false alarm given feature is absent (0 < pfa < 1)
  void updatePositive(double pd, double pfa);

  // Call when the sensor was in observation range but did NOT detect anything.
  void updateNegative(double pd, double pfa);

  // Multiply log-odds by alpha.  Use alpha < 1 (e.g. 0.95) to let beliefs
  // decay towards 50/50 over time when the sensor is no longer observing.
  void decay(double alpha);

  // Reset log-odds to zero (50% prior).
  void reset();

  // --- Query methods ---

  double logOdds()    const { return _L; }

  // P(feature present) = sigmoid(L) = e^L / (1 + e^L)
  double probability() const;

  // Returns true when probability() >= threshold.
  bool decision(double threshold = 0.9) const;

private:
  double _L;  // current log-odds
};
