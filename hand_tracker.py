# =============================================================================
#  hand_tracker.py — Virtual Air Cursor
#  MediaPipe Hands wrapper: landmark detection + drawing helpers.
# =============================================================================

from __future__ import annotations
from typing import List, Dict, Optional
import cv2
import mediapipe as mp
import numpy as np


class HandTracker:
    """Wraps MediaPipe Hands for single-hand landmark detection."""

    def __init__(
        self,
        max_hands: int = 1,
        detection_confidence: float = 0.7,
        tracking_confidence: float = 0.6,
        model_complexity: int = 0,          # 0 = fastest; 1 = accurate
    ) -> None:
        self._mp_hands = mp.solutions.hands
        self._mp_draw  = mp.solutions.drawing_utils
        self._mp_style = mp.solutions.drawing_styles

        self.hands = self._mp_hands.Hands(
            static_image_mode=False,            # Use tracking mode (faster for video)
            max_num_hands=max_hands,
            model_complexity=model_complexity,
            min_detection_confidence=detection_confidence,
            min_tracking_confidence=tracking_confidence,
        )
        self._results = None

    # ──────────────────────────────────────────────────────────────────────────
    def process(self, frame_bgr: np.ndarray) -> List[Dict]:
        """
        Run hand detection on a BGR frame.

        Returns a list (one entry per hand) of landmark lists.
        Each entry is a list of 21 dicts: {id, x, y, z}
        x, y are normalized 0.0–1.0; z is relative depth.
        Returns [] if no hand found.
        """
        frame_rgb  = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        frame_rgb.flags.writeable = False
        self._results = self.hands.process(frame_rgb)
        frame_rgb.flags.writeable = True

        all_hands: List[List[Dict]] = []
        if self._results.multi_hand_landmarks:
            for hand_landmarks in self._results.multi_hand_landmarks:
                landmarks = [
                    {
                        "id": idx,
                        "x": lm.x,
                        "y": lm.y,
                        "z": lm.z,
                    }
                    for idx, lm in enumerate(hand_landmarks.landmark)
                ]
                all_hands.append(landmarks)
        return all_hands

    # ──────────────────────────────────────────────────────────────────────────
    @staticmethod
    def get_tip(landmarks: List[Dict], landmark_id: int) -> Optional[tuple]:
        """Return (x, y) for a specific landmark id, or None if not found."""
        for lm in landmarks:
            if lm["id"] == landmark_id:
                return lm["x"], lm["y"]
        return None

    # ──────────────────────────────────────────────────────────────────────────
    def draw(self, frame: np.ndarray) -> np.ndarray:
        """Draw landmarks and connections onto *frame* (in-place). Returns frame."""
        if self._results and self._results.multi_hand_landmarks:
            for hand_landmarks in self._results.multi_hand_landmarks:
                self._mp_draw.draw_landmarks(
                    frame,
                    hand_landmarks,
                    self._mp_hands.HAND_CONNECTIONS,
                    self._mp_style.get_default_hand_landmarks_style(),
                    self._mp_style.get_default_hand_connections_style(),
                )
        return frame

    # ──────────────────────────────────────────────────────────────────────────
    def release(self) -> None:
        """Free MediaPipe resources."""
        self.hands.close()
