# =============================================================================
#  config.py — Virtual Air Cursor
#  All tunable constants and runtime configuration.
# =============================================================================

import argparse
try:
    from screeninfo import get_monitors
    _monitor = get_monitors()[0]
    SCREEN_WIDTH  = _monitor.width
    SCREEN_HEIGHT = _monitor.height
except Exception:
    SCREEN_WIDTH  = 1920
    SCREEN_HEIGHT = 1080

# ── Camera ────────────────────────────────────────────────────────────────────
CAMERA_INDEX  = 0
FRAME_WIDTH   = 1280
FRAME_HEIGHT  = 720 

# ── Smoothing ─────────────────────────────────────────────────────────────────
SMOOTH_BUFFER_SIZE = 7          # Rolling-average window (frames)

# ── Gesture thresholds ────────────────────────────────────────────────────────
PINCH_CLICK_THRESHOLD = 0.045   # Normalized distance → click
PINCH_DRAG_HOLD_TIME  = 0.5     # Seconds pinch must be held to start drag
CLICK_COOLDOWN        = 0.3     # Seconds between consecutive clicks
SCROLL_SENSITIVITY    = 20      # Pixels scrolled per unit Y-delta

# ── Coordinate mapping ────────────────────────────────────────────────────────
DEAD_ZONE_MARGIN    = 0.05      # Fraction of frame edge to ignore
CURSOR_SPEED_FACTOR = 1.2       # Multiplier on raw movement delta

# ── Display ───────────────────────────────────────────────────────────────────
SHOW_LANDMARKS = True           # Draw hand landmarks in preview window
SHOW_OVERLAY   = True           # Show gesture HUD on preview window

# ── PyAutoGUI tuning ──────────────────────────────────────────────────────────
import pyautogui
pyautogui.PAUSE    = 0.0        # No inter-call sleep
pyautogui.FAILSAFE = False      # Disable corner-of-screen emergency stop


# ── CLI override helper ───────────────────────────────────────────────────────
def parse_args() -> argparse.Namespace:
    """Allow runtime override of key config values via CLI flags."""
    parser = argparse.ArgumentParser(description="Virtual Air Cursor — hand-gesture mouse controller")
    parser.add_argument("--camera",       type=int,   default=CAMERA_INDEX,          help="Webcam index (default 0)")
    parser.add_argument("--smooth",       type=int,   default=SMOOTH_BUFFER_SIZE,    help="Smoothing buffer size")
    parser.add_argument("--pinch",        type=float, default=PINCH_CLICK_THRESHOLD, help="Pinch distance threshold")
    parser.add_argument("--sensitivity",  type=int,   default=SCROLL_SENSITIVITY,    help="Scroll sensitivity")
    parser.add_argument("--no-landmarks", action="store_true",                        help="Hide landmark overlay")
    parser.add_argument("--no-overlay",   action="store_true",                        help="Hide gesture HUD")
    return parser.parse_args()
