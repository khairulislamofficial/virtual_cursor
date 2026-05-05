# =============================================================================
#  main.py — Virtual Air Cursor
#  Entry point: wires all modules together in the main capture/event loop.
# =============================================================================

from __future__ import annotations
import sys
import cv2

import config
from config       import parse_args
from hand_tracker import HandTracker
from smoother     import CoordinateSmoother
from gesture      import Gesture, GestureClassifier, INDEX_TIP
from cursor       import CursorController
from overlay      import HUDOverlay


# ─────────────────────────────────────────────────────────────────────────────
def main() -> None:
    # ── CLI overrides ─────────────────────────────────────────────────────────
    args = parse_args()

    show_landmarks = not args.no_landmarks and config.SHOW_LANDMARKS
    show_overlay   = not args.no_overlay   and config.SHOW_OVERLAY

    # ── Module initialisation ─────────────────────────────────────────────────
    tracker    = HandTracker()
    smoother   = CoordinateSmoother(buffer_size=args.smooth)
    classifier = GestureClassifier(
        pinch_threshold=args.pinch,
        drag_hold_time=config.PINCH_DRAG_HOLD_TIME,
        click_cooldown=config.CLICK_COOLDOWN,
    )
    cursor  = CursorController()
    hud     = HUDOverlay()

    # ── Camera setup ──────────────────────────────────────────────────────────
    cap = cv2.VideoCapture(args.camera, cv2.CAP_DSHOW)   # CAP_DSHOW = faster on Windows
    if not cap.isOpened():
        print(f"[ERROR] Cannot open camera index {args.camera}.")
        sys.exit(1)

    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  config.FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.FRAME_HEIGHT)
    cap.set(cv2.CAP_PROP_FPS, 30)

    print("=" * 56)
    print("  Virtual Air Cursor — running.  Press [Q] to quit.")
    print("=" * 56)
    print(f"  Screen  : {config.SCREEN_WIDTH} x {config.SCREEN_HEIGHT}")
    print(f"  Camera  : {config.FRAME_WIDTH}  x {config.FRAME_HEIGHT}  (index {args.camera})")
    print(f"  Smooth  : buffer size = {args.smooth}")
    print(f"  Pinch   : threshold   = {args.pinch}")
    print("=" * 56)

    # ── Main loop ─────────────────────────────────────────────────────────────
    while True:
        ret, frame = cap.read()
        if not ret:
            print("[WARN] Dropped frame — retrying …")
            continue

        # Mirror horizontally so it feels like a mirror / natural control
        frame = cv2.flip(frame, 1)

        # ── Hand detection ────────────────────────────────────────────────────
        all_hands = tracker.process(frame)
        landmarks = all_hands[0] if all_hands else []

        # ── Coordinate smoothing ──────────────────────────────────────────────
        if landmarks:
            tip = HandTracker.get_tip(landmarks, INDEX_TIP)
            if tip:
                sx, sy = smoother.smooth(tip[0], tip[1])
            else:
                sx, sy = 0.5, 0.5
        else:
            smoother.reset()
            sx, sy = 0.5, 0.5

        # ── Gesture classification ────────────────────────────────────────────
        gesture = classifier.classify(landmarks)

        # ── Cursor actions ────────────────────────────────────────────────────
        match gesture:
            case Gesture.MOVE:
                if cursor.is_dragging:
                    cursor.drag_update(sx, sy)
                else:
                    cursor.move(sx, sy)

            case Gesture.LEFT_CLICK:
                cursor.click("left")
                hud.flash(Gesture.LEFT_CLICK)

            case Gesture.RIGHT_CLICK:
                cursor.right_click()
                hud.flash(Gesture.RIGHT_CLICK)

            case Gesture.DRAG_START:
                cursor.drag_start(sx, sy)
                hud.flash(Gesture.DRAG_START)

            case Gesture.DRAG_END:
                cursor.drag_end()
                hud.flash(Gesture.DRAG_END)

            case Gesture.SCROLL:
                cursor.scroll(classifier.scroll_delta)
                cursor.move(sx, sy)   # Keep cursor in place while scrolling

            case Gesture.FREEZE:
                pass   # Do nothing — cursor is paused

            case Gesture.NONE:
                pass   # No hand — do nothing

        # ── Draw landmark overlay ─────────────────────────────────────────────
        if show_landmarks:
            tracker.draw(frame)

        # ── Draw HUD ──────────────────────────────────────────────────────────
        if show_overlay:
            hud.draw(frame, gesture, classifier.scroll_delta)

        # ── Show preview window ───────────────────────────────────────────────
        cv2.imshow("Virtual Air Cursor", frame)

        # ── Exit on Q ────────────────────────────────────────────────────────
        if cv2.waitKey(1) & 0xFF == ord("q"):
            print("[INFO] Quit key pressed — shutting down.")
            break

    # ── Cleanup ───────────────────────────────────────────────────────────────
    if cursor.is_dragging:
        cursor.drag_end()   # Safety: release mouse button on exit

    cap.release()
    tracker.release()
    cv2.destroyAllWindows()
    print("[INFO] Virtual Air Cursor stopped.")


# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    main()
