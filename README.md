# Project Whiteboard

Project Whiteboard turns any flat surface into a touchless input device. A
camera watches the surface, tracks your hand, and translates gestures into
real mouse and keyboard input on your computer — point to move the cursor,
pinch to click and drag.

## Requirements

- Python 3.9+
- [uv](https://docs.astral.sh/uv/)
- A webcam (optional — the app runs on synthetic demo data if none is found)
- **macOS only:** your terminal app needs Accessibility permission
  (System Settings → Privacy & Security → Accessibility), or mouse/keyboard
  control will silently do nothing.

## Installation

```bash
uv sync
```

## Usage

```bash
uv run python -m src.main
```

On first launch, use the **Calibration** panel to map your camera view to
your screen — pick a mode (automatic edge detection, red stickers, or manual
corner clicks) and click **Start Calibration**. Once calibrated, point at the
screen to move the cursor and pinch to click/drag.
