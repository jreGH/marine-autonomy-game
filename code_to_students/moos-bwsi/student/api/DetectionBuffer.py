"""
DetectionBuffer.py — Bayesian log-odds belief tracker (Python)

Mirrors the C++ BeliefState class in libBWSI so that Python students can
perform the same sensor-fusion calculations as the C++ track.

Usage::

    from api import DetectionBuffer

    buf = DetectionBuffer(pd=0.7, pfa=0.02, decay=0.98)

    # --- inside your main loop ---
    for msg in new_detect_messages:
        detect = parse_detection(msg)
        if detect.confidence > 0.3:     # use the confidence field from
            buf.update_positive()        # pInfrastructureSensor
        else:
            buf.update_negative()

    buf.tick_decay()   # call once per loop iteration

    if buf.decision(threshold=0.85):
        api.notify("ANOMALY_REPORT_JELLYFISH", ...)
        buf.reset()
"""

import math


class DetectionBuffer:
    """Log-odds Bayesian belief state for binary detection decisions.

    Parameters
    ----------
    pd : float
        Probability of detection given the feature is present.
        Must be in (0, 1).
    pfa : float
        Probability of false alarm given the feature is absent.
        Must be in (0, 1).
    decay : float
        Multiplicative factor applied to the log-odds each call to
        ``tick_decay()``.  Use values slightly below 1 (e.g. 0.95–0.99)
        to gradually forget old observations.  1.0 means no decay.
    initial_log_odds : float
        Starting log-odds value (default 0 → 50% prior).
    """

    def __init__(self, pd: float = 0.7, pfa: float = 0.02,
                 decay: float = 1.0, initial_log_odds: float = 0.0):
        self._pd    = max(1e-9, min(1.0 - 1e-9, pd))
        self._pfa   = max(1e-9, min(1.0 - 1e-9, pfa))
        self._decay = decay
        self._L     = initial_log_odds

    # ------------------------------------------------------------------
    # Update methods
    # ------------------------------------------------------------------

    def update_positive(self, pd: float = None, pfa: float = None) -> None:
        """Register a positive detection.

        Optional *pd* and *pfa* override the instance defaults for this
        single update — useful when the ``confidence`` field in an
        ``INFRASTRUCTURE_DETECT`` message provides a per-observation P_D.
        """
        pd  = pd  if pd  is not None else self._pd
        pfa = pfa if pfa is not None else self._pfa
        pd  = max(1e-9, min(1.0 - 1e-9, pd))
        pfa = max(1e-9, min(1.0 - 1e-9, pfa))
        self._L += math.log(pd / pfa)

    def update_negative(self, pd: float = None, pfa: float = None) -> None:
        """Register a null observation (sensor in range; nothing detected)."""
        pd  = pd  if pd  is not None else self._pd
        pfa = pfa if pfa is not None else self._pfa
        pd  = max(1e-9, min(1.0 - 1e-9, pd))
        pfa = max(1e-9, min(1.0 - 1e-9, pfa))
        self._L += math.log((1.0 - pd) / (1.0 - pfa))

    def tick_decay(self) -> None:
        """Apply one decay step.  Call once per main-loop iteration."""
        self._L *= self._decay

    def reset(self) -> None:
        """Reset log-odds to zero (50/50 prior)."""
        self._L = 0.0

    # ------------------------------------------------------------------
    # Query methods
    # ------------------------------------------------------------------

    def log_odds(self) -> float:
        """Current log-odds value L."""
        return self._L

    def probability(self) -> float:
        """P(feature present) = sigmoid(L), clamped to avoid overflow."""
        clamped = max(-30.0, min(30.0, self._L))
        e = math.exp(clamped)
        return e / (1.0 + e)

    def decision(self, threshold: float = 0.9) -> bool:
        """Return True when ``probability() >= threshold``."""
        return self.probability() >= threshold

    def __repr__(self) -> str:
        return (f"DetectionBuffer(L={self._L:.3f}, "
                f"P={self.probability():.3f}, "
                f"pd={self._pd}, pfa={self._pfa})")
