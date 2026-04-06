/************************************************************/
/*    FILE: BeliefState.cpp                                 */
/*    ORGN: BWSI AUVC                                       */
/************************************************************/
#include "BeliefState.h"
#include <algorithm>
#include <stdexcept>

BeliefState::BeliefState(double initialLogOdds)
  : _L(initialLogOdds) {}

void BeliefState::updatePositive(double pd, double pfa) {
  // Clamp to avoid log(0)
  pd  = std::max(1e-6, std::min(1.0 - 1e-6, pd));
  pfa = std::max(1e-6, std::min(1.0 - 1e-6, pfa));
  _L += std::log(pd / pfa);
}

void BeliefState::updateNegative(double pd, double pfa) {
  pd  = std::max(1e-6, std::min(1.0 - 1e-6, pd));
  pfa = std::max(1e-6, std::min(1.0 - 1e-6, pfa));
  _L += std::log((1.0 - pd) / (1.0 - pfa));
}

void BeliefState::decay(double alpha) {
  _L *= alpha;
}

void BeliefState::reset() {
  _L = 0.0;
}

double BeliefState::probability() const {
  // sigmoid: clamp exponent to avoid overflow
  double e = std::exp(std::max(-30.0, std::min(30.0, _L)));
  return e / (1.0 + e);
}

bool BeliefState::decision(double threshold) const {
  return probability() >= threshold;
}
