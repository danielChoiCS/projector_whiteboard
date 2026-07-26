"""Mock providers that let the GUI run before vision/calibration exist.

These stand in for the real vision and calibration subsystems. They satisfy
the same HandProvider / CalibrationProvider interfaces, so main.py can swap
them for real implementations later with no changes to the GUI.
"""

import time
from itertools import cycle

from PySide6.QtCore import QTimer

from src.gui.providers.base import CalibrationProvider, HandProvider
from src.models import CalibrationState, Gesture, HandState

_HAND_SCENARIOS: list[HandState] = [
    HandState(detected=False, x=0.0, y=0.0, gesture=Gesture.NONE, confidence=0.0, timestamp=0.0),
    HandState(detected=True, x=0.5, y=0.3, gesture=Gesture.MOVE, confidence=0.95, timestamp=0.0),
    HandState(detected=True, x=0.6, y=0.35, gesture=Gesture.CLICK, confidence=0.9, timestamp=0.0),
    HandState(detected=True, x=0.4, y=0.5, gesture=Gesture.DRAG, confidence=0.8, timestamp=0.0),
    HandState(detected=True, x=0.45, y=0.55, gesture=Gesture.SCROLL, confidence=0.7, timestamp=0.0),
]

_MOCK_STEP_INTERVAL_MS = 1500
_CALIBRATION_STEP_INTERVAL_MS = 400
_CALIBRATION_STEP_SIZE = 0.1


class MockHandProvider(HandProvider):
    """Cycles through sample HandState scenarios on a timer."""

    def __init__(self) -> None:
        super().__init__()
        self._scenarios = cycle(_HAND_SCENARIOS)
        self._timer = QTimer(self)
        self._timer.setInterval(_MOCK_STEP_INTERVAL_MS)
        self._timer.timeout.connect(self._emit_next)

    def start(self) -> None:
        """Begin cycling through sample hand states."""
        self._emit_next()
        self._timer.start()

    def stop(self) -> None:
        """Stop cycling through sample hand states."""
        self._timer.stop()

    def _emit_next(self) -> None:
        sample = next(self._scenarios)
        state = HandState(
            detected=sample.detected,
            x=sample.x,
            y=sample.y,
            gesture=sample.gesture,
            confidence=sample.confidence,
            timestamp=time.time(),
        )
        self.hand_state_changed.emit(state)


class MockCalibrationProvider(CalibrationProvider):
    """Simulates a calibration pass that progresses over a few seconds."""

    def __init__(self) -> None:
        super().__init__()
        self._progress = 0.0
        self._timer = QTimer(self)
        self._timer.setInterval(_CALIBRATION_STEP_INTERVAL_MS)
        self._timer.timeout.connect(self._advance)

    def start_calibration(self) -> None:
        """Begin the simulated calibration pass."""
        self._progress = 0.0
        self._emit(in_progress=True, message="Calibrating...")
        self._timer.start()

    def _advance(self) -> None:
        self._progress = min(1.0, self._progress + _CALIBRATION_STEP_SIZE)
        if self._progress >= 1.0:
            self._timer.stop()
            self._emit(in_progress=False, message="Calibration complete")
        else:
            self._emit(in_progress=True, message="Calibrating...")

    def _emit(self, in_progress: bool, message: str) -> None:
        calibrated = self._progress >= 1.0
        state = CalibrationState(
            calibrated=calibrated,
            in_progress=in_progress,
            progress=self._progress,
            transform_available=calibrated,
            status_message=message,
        )
        self.calibration_state_changed.emit(state)
