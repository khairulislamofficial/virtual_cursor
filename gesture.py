# =============================================================================
#  gesture.py — Virtual Air Cursor
#  GestureClassifier: maps MediaPipe landmarks → Gesture enum.
# =============================================================================

from __future__ import annotations
from enum import Enum, auto
from typing import List, Dict, Optional
import math
import time

import config


# ─────────────────────────────────────────────────────────────────────────────
#  Gesture enum
# ─────────────────────────────────────────────────────────────────────────────

class Gesture(Enum):
    NONE        = auto()   # No hand detected
    MOVE        = auto()   # Index finger up → move cursor
    LEFT_CLICK  = auto()   # Pinch (index + thumb) released
    RIGHT_CLICK = auto()   # Pinch (middle + thumb) released
    DRAG_START  = auto()   # Pinch held > PINCH_DRAG_HOLD_TIME
    DRAG_END    = auto()   # Pinch released after drag
    SCROLL      = auto()   # Index + middle up → scroll
    FREEZE      = auto()   # Fist → freeze cursor


# ─────────────────────────────────────────────────────────────────────────────
#  Landmark ID constants (MediaPipe 21-point model)
# ─────────────────────────────────────────────────────────────────────────────

WRIST      = 0
THUMB_TIP  = 4
INDEX_MCP  = 5;  INDEX_PIP  = 6;  INDEX_TIP  = 8
MIDDLE_MCP = 9;  MIDDLE_PIP = 10; MIDDLE_TIP = 12
RING_MCP   = 13; RING_PIP   = 14; RING_TIP   = 16
PINKY_MCP  = 17; PINKY_PIP  = 18; PINKY_TIP  = 20


# ─────────────────────────────────────────────────────────────────────────────
#  Classifier
# ─────────────────────────────────────────────────────────────────────────────

class GestureClassifier:
    """
    Stateful gesture classifier.

    State is maintained across frames so that:
      - Clicks only fire on RELEASE (not while pinching).
      - Drag is triggered after a sustained pinch.
      - Scroll uses the vertical delta between frames.
    """

    def __init__(
        self,
        pinch_threshold: float = config.PINCH_CLICK_THRESHOLD,
        drag_hold_time:  float = config.PINCH_DRAG_HOLD_TIME,
        click_cooldown:  float = config.CLICK_COOLDOWN,
    ) -> None:
        self._pinch_threshold = pinch_threshold
        self._drag_hold_time  = drag_hold_time
        self._click_cooldown  = click_cooldown

        # ── Left-click / drag state ──────────────────────────────────────────
        self._left_pinch_active:  bool  = False
        self._left_pinch_start:   float = 0.0
        self._drag_active:        bool  = False
        self._last_click_time:    float = 0.0

        # ── Right-click state ────────────────────────────────────────────────
        self._right_pinch_active: bool  = False
        self._last_right_time:    float = 0.0

        # ── Scroll state ─────────────────────────────────────────────────────
        self._scroll_prev_y: Optional[float] = None
        self.scroll_delta:   float = 0.0        # Exposed to main.py

    # ──────────────────────────────────────────────────────────────────────────
    def classify(self, landmarks: List[Dict]) -> Gesture:
        """
        Classify the current frame's gesture.

        Parameters
        ----------
        landmarks : List of 21 landmark dicts {id, x, y, z}, or empty list.

        Returns
        -------
        Gesture enum value
        """
        if not landmarks:
            self._reset_state()
            return Gesture.NONE

        now = time.time()

        # ── 1. Finger up/down state ──────────────────────────────────────────
        index_up  = self._finger_up(landmarks, INDEX_TIP,  INDEX_PIP)
        middle_up = self._finger_up(landmarks, MIDDLE_TIP, MIDDLE_PIP)
        ring_up   = self._finger_up(landmarks, RING_TIP,   RING_PIP)
        pinky_up  = self._finger_up(landmarks, PINKY_TIP,  PINKY_PIP)

        # ── 2. Fist detection → FREEZE ───────────────────────────────────────
        if not index_up and not middle_up and not ring_up and not pinky_up:
            self._reset_state()
            return Gesture.FREEZE

        # ── 3. Left pinch (thumb ↔ index) ────────────────────────────────────
        left_dist = self._distance_by_id(landmarks, THUMB_TIP, INDEX_TIP)
        left_pinching = left_dist < self._pinch_threshold

        if left_pinching:
            if not self._left_pinch_active:
                # Pinch just started
                self._left_pinch_active = True
                self._left_pinch_start  = now

            elapsed = now - self._left_pinch_start
            if elapsed >= self._drag_hold_time and not self._drag_active:
                self._drag_active = True
                return Gesture.DRAG_START
            if self._drag_active:
                return Gesture.MOVE   # Continue drag (cursor.drag_update called in main)

        else:
            if self._left_pinch_active:
                # Pinch just released
                self._left_pinch_active = False
                if self._drag_active:
                    self._drag_active = False
                    return Gesture.DRAG_END
                else:
                    # Fire left click on release (with cooldown)
                    if now - self._last_click_time >= self._click_cooldown:
                        self._last_click_time = now
                        return Gesture.LEFT_CLICK

        # ── 4. Right pinch (thumb ↔ middle) ──────────────────────────────────
        right_dist     = self._distance_by_id(landmarks, THUMB_TIP, MIDDLE_TIP)
        right_pinching = right_dist < self._pinch_threshold

        if right_pinching:
            self._right_pinch_active = True
        else:
            if self._right_pinch_active:
                self._right_pinch_active = False
                if now - self._last_right_time >= self._click_cooldown:
                    self._last_right_time = now
                    return Gesture.RIGHT_CLICK

        # ── 5. Scroll (index + middle up, others down) ────────────────────────
        if index_up and middle_up and not ring_up and not pinky_up:
            tip = self._get_lm(landmarks, INDEX_TIP)
            if tip:
                curr_y = tip["y"]
                if self._scroll_prev_y is not None:
                    self.scroll_delta = (curr_y - self._scroll_prev_y) * 1000
                self._scroll_prev_y = curr_y
            return Gesture.SCROLL

        # Reset scroll anchor when not scrolling
        self._scroll_prev_y = None
        self.scroll_delta   = 0.0

        # ── 6. Default → MOVE ────────────────────────────────────────────────
        return Gesture.MOVE

    # ──────────────────────────────────────────────────────────────────────────
    #  Internal helpers
    # ──────────────────────────────────────────────────────────────────────────

    @staticmethod
    def _get_lm(landmarks: List[Dict], lm_id: int) -> Optional[Dict]:
        for lm in landmarks:
            if lm["id"] == lm_id:
                return lm
        return None

    @staticmethod
    def _finger_up(landmarks: List[Dict], tip_id: int, pip_id: int) -> bool:
        """
        A finger is considered UP when its TIP y-coordinate is above (less than)
        its PIP y-coordinate.  In OpenCV image coords, y increases downward.
        """
        tip = None; pip = None
        for lm in landmarks:
            if lm["id"] == tip_id: tip = lm
            if lm["id"] == pip_id: pip = lm
        if tip is None or pip is None:
            return False
        return tip["y"] < pip["y"]

    @staticmethod
    def _distance(p1: Dict, p2: Dict) -> float:
        """Euclidean distance in normalized coordinate space."""
        return math.sqrt((p1["x"] - p2["x"]) ** 2 + (p1["y"] - p2["y"]) ** 2)

    def _distance_by_id(self, landmarks: List[Dict], id1: int, id2: int) -> float:
        lm1 = self._get_lm(landmarks, id1)
        lm2 = self._get_lm(landmarks, id2)
        if lm1 is None or lm2 is None:
            return 1.0   # Large value → not pinching
        return self._distance(lm1, lm2)

    def _reset_state(self) -> None:
        """Clear all transient state when hand is lost."""
        self._left_pinch_active  = False
        self._drag_active        = False
        self._right_pinch_active = False
        self._scroll_prev_y      = None
        self.scroll_delta        = 0.0
