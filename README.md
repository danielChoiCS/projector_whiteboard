# Project Whiteboard

A Python computer vision system that turns any flat surface into a touchless
input device. A camera watches the surface; hand gestures are translated into
mouse and keyboard input on the host computer.

```
Camera Feed
    |
    v
OpenCV Camera
    |
    +----------------+
    |                |
    v                v
Vision          Calibration
(MediaPipe)     (Mapping)
    |                |
    +-------+--------+
            |
            v
      Input Controller
       (PyAutoGUI)
```

The GUI observes all of this through shared data models only — it never
calls MediaPipe, processes OpenCV frames, runs calibration math, or drives
the mouse directly.

## Tech stack

- Python 3.9
- PySide6 (GUI)
- OpenCV, MediaPipe, PyAutoGUI (vision / calibration / input — not yet implemented)
- `uv` for dependency management

## Directory structure

```
src/
  models/       Shared data structures. No PySide6/OpenCV/MediaPipe imports.
  gui/          PySide6 application. Only imports src.models.
    widgets/    Dumb display widgets (one update_x(state) slot each).
    providers/  Interfaces + mock data sources the GUI runs against today.
  vision/       (not yet implemented) MediaPipe hand tracking, gesture recognition.
  calibration/  (not yet implemented) Surface detection, perspective transform.
  control/      (not yet implemented) Converts commands into PyAutoGUI calls.
  main.py       Entry point.
```

Each top-level package under `src/` is owned independently and only depends
on `src/models`:

```
vision       -> models
calibration  -> models
control      -> models
gui          -> models
```

`gui` must never import `vision`, `calibration`, or `control` directly.
Modules never move between packages; cross-module changes go through
`src/models` or an adapter, not a rewrite of someone else's code.

## Data flow

`src/models/` defines the only vocabulary the subsystems share:

- **`HandState`** — detection flag, normalized position, `Gesture`, confidence,
  timestamp. Produced by `vision`.
- **`CalibrationState`** — calibrated flag, in-progress flag, progress,
  transform availability, status text. Produced by `calibration`.
- **`ApplicationState`** — aggregate `SystemState`, camera/tracking/calibration
  flags, and a status message. Derived by the GUI from the two states above.

These are plain, frozen dataclasses — no Qt, no dictionaries, no globals.
Any subsystem can produce them without depending on PySide6.

`src/gui/providers/base.py` defines the one Qt-flavored contract in the
project: `HandProvider` and `CalibrationProvider`, each a `QObject` that
emits its model over a signal (`hand_state_changed`, `calibration_state_changed`).
This is the seam where `vision` and `calibration` plug in — a real provider
runs its processing on a worker `QThread` and emits the same signals a mock
does.

`src/gui/main_window.py` is the only place that coordinates across widgets:
it subscribes to both provider signals, updates the relevant widget via its
`update_x(state)` slot, and derives `ApplicationState` from the latest
`HandState`/`CalibrationState`. Every widget in `src/gui/widgets/` is
otherwise inert — it renders whatever state it's handed and holds no
processing logic of its own.

## Running today, without vision/calibration/control

`vision`, `calibration`, and `control` don't exist yet. `src/main.py` wires
`MockHandProvider` and `MockCalibrationProvider` (`src/gui/providers/mock.py`)
into the GUI instead:

- `MockHandProvider` cycles through sample hand/gesture states on a `QTimer`.
- `MockCalibrationProvider` simulates calibration progress advancing over a
  few seconds when "Start Calibration" is clicked.

Because both mocks satisfy the exact same `HandProvider`/`CalibrationProvider`
interface a real implementation will, swapping them out later is a one-line
change in `src/main.py` — `src/gui` and `src/models` don't change.

```bash
uv sync
uv run python -m src.main
```

## Threading

- **Main thread:** PySide6 GUI only.
- **Worker threads (future):** camera capture, MediaPipe inference,
  calibration processing.
- Communication crosses thread boundaries via Qt signals/slots only — no
  processing loops inside GUI widgets.

## Coding rules

- Type hints and docstrings on all public functions/classes.
- No dictionaries for cross-module data — use the models in `src/models`.
- No global state.
- Small, independent modules; don't change another module's public
  interface without discussion.
