# =============================================================================
#  overlay.py — Virtual Air Cursor
#  HUD overlay drawn on the OpenCV preview window.
# =============================================================================

from __future__ import annotations
import time
import cv2
import numpy as np
from gesture import Gesture


# ── Colour palette ─────────────────────────────────────────────────────────────
_COLOURS: dict[Gesture, tuple[int, int, int]] = {
    Gesture.NONE:        (80,  80,  80),
    Gesture.MOVE:        (50, 220, 50),
    Gesture.LEFT_CLICK:  (50, 150, 255),
    Gesture.RIGHT_CLICK: (50,  50, 255),
    Gesture.DRAG_START:  (200, 100, 255),
    Gesture.DRAG_END:    (200, 100, 255),
    Gesture.SCROLL:      (255, 200,  50),
    Gesture.FREEZE:      (50,  50,  200),
}

_LABELS: dict[Gesture, str] = {
    Gesture.NONE:        "⬜  No Hand",
    Gesture.MOVE:        "🖱  Move",
    Gesture.LEFT_CLICK:  "🖱  Left Click",
    Gesture.RIGHT_CLICK: "🖱  Right Click",
    Gesture.DRAG_START:  "✊  Drag",
    Gesture.DRAG_END:    "✊  Drop",
    Gesture.SCROLL:      "↕  Scroll",
    Gesture.FREEZE:      "✊  Freeze",
}


class HUDOverlay:
    """
    Draws a gesture-state HUD and live FPS counter onto an OpenCV frame.
    Call draw() once per frame after gesture classification.
    """

    def __init__(self) -> None:
        self._frame_times: list[float] = []
        self._flash_gesture: Gesture | None = None
        self._flash_until:   float = 0.0

    # ──────────────────────────────────────────────────────────────────────────
    def flash(self, gesture: Gesture, duration: float = 0.35) -> None:
        """Trigger a brief visual flash (for click/drag events)."""
        self._flash_gesture = gesture
        self._flash_until   = time.time() + duration

    # ──────────────────────────────────────────────────────────────────────────
    def draw(
        self,
        frame: np.ndarray,
        gesture: Gesture,
        scroll_delta: float = 0.0,
    ) -> np.ndarray:
        """
        Render gesture label, FPS counter, and optional scroll indicator
        onto *frame* (in-place).  Returns the frame.
        """
        now = time.time()
        h, w = frame.shape[:2]

        # ── FPS tracking ──────────────────────────────────────────────────────
        self._frame_times.append(now)
        self._frame_times = [t for t in self._frame_times if now - t < 1.0]
        fps = len(self._frame_times)

        # ── Decide displayed gesture (flash overrides) ────────────────────────
        display_gesture = gesture
        if self._flash_gesture and now < self._flash_until:
            display_gesture = self._flash_gesture
        elif now >= self._flash_until:
            self._flash_gesture = None

        colour = _COLOURS.get(display_gesture, (200, 200, 200))
        label  = _LABELS.get(display_gesture,  "Unknown")

        # ── Bottom-left panel ─────────────────────────────────────────────────
        panel_h, panel_w = 64, 260
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, h - panel_h), (panel_w, h), (20, 20, 20), -1)
        cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)

        # Gesture colour bar
        cv2.rectangle(frame, (0, h - panel_h), (6, h), colour, -1)

        # Gesture label text
        cv2.putText(
            frame, label,
            (14, h - panel_h + 26),
            cv2.FONT_HERSHEY_SIMPLEX, 0.65, colour, 2, cv2.LINE_AA,
        )

        # FPS counter
        fps_colour = (80, 220, 80) if fps >= 20 else (50, 50, 220)
        cv2.putText(
            frame, f"FPS: {fps}",
            (14, h - panel_h + 50),
            cv2.FONT_HERSHEY_SIMPLEX, 0.52, fps_colour, 1, cv2.LINE_AA,
        )

        # ── Scroll indicator ──────────────────────────────────────────────────
        if gesture == Gesture.SCROLL and abs(scroll_delta) > 0.5:
            direction = "▼ Scroll Down" if scroll_delta > 0 else "▲ Scroll Up"
            cv2.putText(
                frame, direction,
                (w - 180, h - 20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 200, 50), 2, cv2.LINE_AA,
            )

        # ── Top-right corner: drag indicator ─────────────────────────────────
        if display_gesture in (Gesture.DRAG_START, Gesture.DRAG_END):
            cv2.putText(
                frame, "DRAG ACTIVE",
                (w - 190, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 100, 255), 2, cv2.LINE_AA,
            )

        return frame
