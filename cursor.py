# =============================================================================
#  cursor.py — Virtual Air Cursor
#  CursorController: maps normalized landmark coords → screen actions.
# =============================================================================

from __future__ import annotations
import pyautogui
import config


class CursorController:
    """
    Maps normalized (0.0–1.0) hand coordinates to pixel-space mouse actions.

    Dead-zone clipping removes the outer `margin` fraction of the frame
    so the cursor reaches screen edges without the hand leaving the camera.
    """

    def __init__(
        self,
        screen_w:  int = config.SCREEN_WIDTH,
        screen_h:  int = config.SCREEN_HEIGHT,
        frame_w:   int = config.FRAME_WIDTH,
        frame_h:   int = config.FRAME_HEIGHT,
        margin:    float = config.DEAD_ZONE_MARGIN,
    ) -> None:
        self._sw     = screen_w
        self._sh     = screen_h
        self._fw     = frame_w
        self._fh     = frame_h
        self._margin = margin

        self._dragging = False

    # ──────────────────────────────────────────────────────────────────────────
    #  Public API
    # ──────────────────────────────────────────────────────────────────────────

    def move(self, norm_x: float, norm_y: float) -> None:
        """Move mouse cursor to the screen position mapped from (norm_x, norm_y)."""
        px, py = self._map(norm_x, norm_y)
        pyautogui.moveTo(px, py)

    def click(self, button: str = "left") -> None:
        """Fire a single mouse click."""
        pyautogui.click(button=button)

    def right_click(self) -> None:
        """Fire a right-click at the current cursor position."""
        pyautogui.rightClick()

    def drag_start(self, norm_x: float, norm_y: float) -> None:
        """Begin a drag (mouseDown) at the mapped position."""
        px, py = self._map(norm_x, norm_y)
        pyautogui.mouseDown(px, py, button="left")
        self._dragging = True

    def drag_update(self, norm_x: float, norm_y: float) -> None:
        """Continue dragging by moving to the new mapped position."""
        if self._dragging:
            px, py = self._map(norm_x, norm_y)
            pyautogui.moveTo(px, py)

    def drag_end(self) -> None:
        """End the drag (mouseUp)."""
        if self._dragging:
            pyautogui.mouseUp(button="left")
            self._dragging = False

    def scroll(self, delta_y: float) -> None:
        """
        Scroll vertically.

        Positive delta_y  → hand moved down  → scroll DOWN (negative clicks).
        Negative delta_y  → hand moved up    → scroll UP   (positive clicks).
        """
        clicks = -int(delta_y / config.SCROLL_SENSITIVITY)
        if clicks != 0:
            pyautogui.scroll(clicks)

    @property
    def is_dragging(self) -> bool:
        return self._dragging

    # ──────────────────────────────────────────────────────────────────────────
    #  Internal helpers
    # ──────────────────────────────────────────────────────────────────────────

    def _map(self, norm_x: float, norm_y: float) -> tuple[int, int]:
        """
        Map normalized coords (0–1) to screen pixels, applying dead-zone.

        Dead-zone removes `margin` from each edge so the usable input area
        maps to the full screen, making it easy to reach corners.
        """
        m = self._margin

        # Clamp to [margin, 1-margin]
        cx = max(m, min(1.0 - m, norm_x))
        cy = max(m, min(1.0 - m, norm_y))

        # Rescale to [0, 1]
        sx = (cx - m) / (1.0 - 2 * m)
        sy = (cy - m) / (1.0 - 2 * m)

        # Map to screen pixels (mirror X because webcam is flipped)
        px = int(sx * self._sw)
        py = int(sy * self._sh)

        # Clamp to screen bounds
        px = max(0, min(self._sw - 1, px))
        py = max(0, min(self._sh - 1, py))
        return px, py
