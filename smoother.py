# =============================================================================
#  smoother.py — Virtual Air Cursor
#  Coordinate smoothing: rolling-average and optional OneEuro filter.
# =============================================================================

from __future__ import annotations
from collections import deque
from typing import Tuple
import math
import time


# ─────────────────────────────────────────────────────────────────────────────
#  Rolling-average smoother (primary)
# ─────────────────────────────────────────────────────────────────────────────

class CoordinateSmoother:
    """
    Rolling-average smoother for (x, y) coordinates.

    Averages the last `buffer_size` positions to reduce jitter.
    """

    def __init__(self, buffer_size: int = 7) -> None:
        self._buf_x: deque[float] = deque(maxlen=buffer_size)
        self._buf_y: deque[float] = deque(maxlen=buffer_size)

    def smooth(self, x: float, y: float) -> Tuple[float, float]:
        """Add a new sample and return the smoothed (x, y)."""
        self._buf_x.append(x)
        self._buf_y.append(y)
        sx = sum(self._buf_x) / len(self._buf_x)
        sy = sum(self._buf_y) / len(self._buf_y)
        return sx, sy

    def reset(self) -> None:
        """Clear the buffer (e.g. when the hand is lost)."""
        self._buf_x.clear()
        self._buf_y.clear()


# ─────────────────────────────────────────────────────────────────────────────
#  OneEuro filter (optional, higher-quality)
# ─────────────────────────────────────────────────────────────────────────────

class _LowPassFilter:
    """Single low-pass filter component used by OneEuroSmoother."""

    def __init__(self) -> None:
        self._y: float | None = None
        self._dy: float = 0.0

    def filter(self, x: float, alpha: float) -> float:
        if self._y is None:
            self._y = x
            return x
        self._dy = x - self._y
        self._y  = alpha * x + (1 - alpha) * self._y
        return self._y

    @property
    def last_value(self) -> float:
        return self._y or 0.0


class OneEuroSmoother:
    """
    OneEuro low-pass filter for smooth, low-latency cursor tracking.

    Parameters
    ----------
    freq        : Nominal sampling frequency in Hz (e.g. 30)
    min_cutoff  : Minimum cutoff frequency (lower → smoother but more lag)
    beta        : Speed coefficient (higher → less lag during fast motion)
    d_cutoff    : Cutoff for the derivative filter (usually 1.0)
    """

    def __init__(
        self,
        freq: float = 30.0,
        min_cutoff: float = 1.0,
        beta: float = 0.007,
        d_cutoff: float = 1.0,
    ) -> None:
        self._freq       = freq
        self._min_cutoff = min_cutoff
        self._beta       = beta
        self._d_cutoff   = d_cutoff

        self._x_filter  = _LowPassFilter()
        self._dx_filter = _LowPassFilter()
        self._y_filter  = _LowPassFilter()
        self._dy_filter = _LowPassFilter()

        self._last_time: float | None = None

    # ── helpers ───────────────────────────────────────────────────────────────
    @staticmethod
    def _alpha(cutoff: float, te: float) -> float:
        tau   = 1.0 / (2 * math.pi * cutoff)
        return 1.0 / (1.0 + tau / te)

    def _filter_axis(
        self,
        x: float,
        lp: _LowPassFilter,
        dlp: _LowPassFilter,
        te: float,
    ) -> float:
        # Derivative estimate
        dx   = (x - lp.last_value) / te if lp.last_value else 0.0
        edx  = dlp.filter(dx, self._alpha(self._d_cutoff, te))
        # Adaptive cutoff
        cutoff = self._min_cutoff + self._beta * abs(edx)
        return lp.filter(x, self._alpha(cutoff, te))

    # ── public ────────────────────────────────────────────────────────────────
    def smooth(
        self,
        x: float,
        y: float,
        timestamp: float | None = None,
    ) -> Tuple[float, float]:
        """Apply OneEuro filter and return smoothed (x, y)."""
        now = timestamp if timestamp is not None else time.time()
        if self._last_time is None:
            te = 1.0 / self._freq
        else:
            te = now - self._last_time
            if te <= 0:
                te = 1.0 / self._freq
        self._last_time = now

        sx = self._filter_axis(x, self._x_filter, self._dx_filter, te)
        sy = self._filter_axis(y, self._y_filter, self._dy_filter, te)
        return sx, sy

    def reset(self) -> None:
        """Reset internal filter state."""
        self._x_filter  = _LowPassFilter()
        self._dx_filter = _LowPassFilter()
        self._y_filter  = _LowPassFilter()
        self._dy_filter = _LowPassFilter()
        self._last_time = None
