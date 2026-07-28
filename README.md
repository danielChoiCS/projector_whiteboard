# Project Whiteboard

A Python computer vision system that turns any flat surface into a touchless
input device. A camera watches the surface, MediaPipe tracks a hand and
classifies its gesture, and that gesture drives drawing/erasing on a virtual
whiteboard today — with mouse/keyboard control (via PyAutoGUI) planned next.

Two ways to run it ship in this repo: a standalone OpenCV draw/erase demo,
and a PySide6 GUI that can run on mock hand/calibration data or on the real
camera pipeline.

## Installation

Requires [git](https://git-scm.com/) and [uv](https://docs.astral.sh/uv/)
(see [Dependencies](#dependencies)).

```bash
git clone https://github.com/danielChoiCS/projector_whiteboard.git
cd projector_whiteboard
uv sync
```

`uv sync` creates a `.venv/` and installs the pinned Python version
(3.9, see `.python-version`) plus every dependency in `pyproject.toml`.

## Usage

```bash
uv run python -m src.app             # GUI, mock hand/calibration data
uv run python -m src.app --camera    # GUI, real camera + MediaPipe tracking, no paint
uv run python -m src.main            # standalone OpenCV whiteboard demo, no GUI, paint
```

- **`src.app`** opens the PySide6 GUI. Without `--camera` it runs against
  canned sample data so the interface is explorable with no camera attached.
  With `--camera`, it drives the GUI from a real camera feed and MediaPipe
  hand tracking; click "Start Calibration" in the panel to run the 4-corner
  click calibration.
- **`src.main`** is the original non-GUI demo: click the drawing surface's 4
  corners on the camera feed to calibrate, then draw with a pointing finger,
  erase with a fist, and hover with an open hand. Press `r` any time to
  re-calibrate, `q` to quit. During calibration: `z` undoes the last corner,
  `c` restarts, `q` cancels.

Both entry points need a working camera at index 0. On first run, `src.main`
and `src.app --camera` download the MediaPipe hand-landmarker model
automatically (requires internet access that first time).

## Dependencies

- **[git](https://git-scm.com/)** — to clone this repository.
- **[uv](https://docs.astral.sh/uv/)** — manages the Python version and all
  dependencies below; no separate `pip install` step is needed.
- **Python 3.9** — installed automatically by `uv sync` if not already
  present.
- **Runtime libraries** (declared in `pyproject.toml`, installed by `uv sync`):
  - `opencv-python` — camera capture, calibration math, drawing.
  - `mediapipe` — hand landmark tracking.
  - `numpy` — array/geometry math.
  - `pyside6` — the GUI.
  - `pyautogui` — planned mouse/keyboard control (not wired up yet).
- **Dev tools** (installed by `uv sync`, not required to just run the app):
  `pytest` for the test suite in `tests/`, `ruff` for linting.
