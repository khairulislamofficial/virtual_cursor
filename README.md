# Virtual Air Cursor 🖱️

Control your PC mouse using **hand gestures** captured by your webcam — no physical mouse required.

Built with **MediaPipe** hand tracking, **OpenCV** video capture, and **PyAutoGUI** mouse control.

---

## Requirements

- Python **3.10+** (uses `match/case` statement)
- A standard USB or built-in webcam
- Windows / macOS / Linux

---

## Installation

```bash
# 1. Clone or download the project
cd virtual-cursor

# 2. (Recommended) Create a virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS / Linux

# 3. Install dependencies
pip install -r requirements.txt
```

---

## Running

```bash
python main.py
```

A **preview window** will open showing your webcam feed with hand landmarks drawn.  
Press **`Q`** to quit.

### CLI Options

| Flag | Default | Description |
|------|---------|-------------|
| `--camera N` | `0` | Webcam index (try `1` for external cam) |
| `--smooth N` | `7` | Smoothing buffer size (higher = smoother but slower) |
| `--pinch F` | `0.045` | Pinch distance threshold (lower = more sensitive) |
| `--sensitivity N` | `20` | Scroll sensitivity |
| `--no-landmarks` | off | Hide landmark dots on preview |
| `--no-overlay` | off | Hide gesture HUD on preview |

**Example:**
```bash
python main.py --camera 1 --smooth 10 --no-landmarks
```

---

## Gesture Reference

| Gesture | Action |
|---------|--------|
| ☝️ Index finger up, others curled | **Move cursor** |
| 🤏 Pinch: index + thumb (release) | **Left click** |
| 🤏 Hold pinch > 0.5 s | **Start drag** |
| 🤏 Release long pinch | **Drop / end drag** |
| ✌️ Index + middle up, others down | **Scroll** (move hand ↑↓) |
| 🤏 Pinch: middle + thumb (release) | **Right click** |
| ✋ Open palm (all fingers spread) | **Pause** (neutral) |
| ✊ Fist (all fingers curled) | **Freeze cursor** (safety pause) |

---

## Project Structure

```
virtual-cursor/
├── main.py           ← Entry point — main capture + event loop
├── hand_tracker.py   ← MediaPipe wrapper, returns landmark dicts
├── gesture.py        ← Gesture classifier → Gesture enum
├── cursor.py         ← Maps coords to screen, calls PyAutoGUI
├── smoother.py       ← Rolling-average + OneEuro filter
├── config.py         ← All tunable constants + CLI arg parser
├── overlay.py        ← HUD: gesture label + FPS counter
├── requirements.txt  ← pip dependencies
└── README.md         ← This file
```

---

## Tuning Tips

| Problem | Fix |
|---------|-----|
| Cursor jitters | Increase `--smooth` to `9–12` |
| Accidental clicks | Raise `--pinch` slightly (e.g. `0.06`) |
| Low FPS / lag | Already using `model_complexity=0`; close other apps |
| Scroll too fast | Raise `SCROLL_SENSITIVITY` in `config.py` |
| Click fires twice | `CLICK_COOLDOWN` in `config.py` (default 0.3 s) |
| Drag feels sticky | Lower `PINCH_DRAG_HOLD_TIME` in `config.py` (e.g. `0.3`) |

---

## How It Works

1. **Capture** — OpenCV reads 640×480 frames from the webcam at ~30 FPS.
2. **Detect** — MediaPipe Hands locates 21 landmarks on the hand.
3. **Smooth** — A rolling-average filter reduces jitter on the index fingertip position.
4. **Classify** — `GestureClassifier` maps landmark geometry to a `Gesture` enum value.
5. **Act** — `CursorController` translates normalized coordinates to screen pixels and calls PyAutoGUI.
6. **Display** — The HUD overlay and landmark dots are drawn on the preview window.

---

## License

MIT — free to use and modify.
