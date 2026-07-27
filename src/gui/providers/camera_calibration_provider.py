"""Real CalibrationProvider: runs the calibration engine on live camera frames."""

from __future__ import annotations

import numpy as np

from src.calibration.engine import CalibrationEngine
from src.gui.providers.base import CalibrationProvider
from src.models import CalibrationMode, CalibrationState


class CameraCalibrationProvider(CalibrationProvider):
    """Runs CalibrationEngine against live camera frames.

    Automatic detection only runs frames through the engine while a
    calibration attempt is active (between start_calibration() and either a
    successful result or a mode switch) and only in an automatic mode --
    manual mode is driven entirely by add_manual_point().
    """

    def __init__(self) -> None:
        super().__init__()
        self._engine = CalibrationEngine()
        self._active = False

    def start_calibration(self) -> None:
        """(Re)start calibration using the engine's currently selected mode."""
        self._engine.reset()
        self._active = True
        self._emit_state()

    def set_mode(self, mode: CalibrationMode) -> None:
        """Switch strategy and discard any in-progress calibration attempt."""
        self._active = False
        self._engine.set_mode(mode)
        self._emit_state()

    def add_manual_point(self, x: float, y: float) -> None:
        """Forward a manually clicked corner to the engine."""
        self._emit_state(self._engine.add_manual_point(x, y))

    def process_frame(self, frame: np.ndarray) -> None:
        """Run the selected automatic detector on one camera frame, if active."""
        if not self._active or self._engine.mode == CalibrationMode.MANUAL_CLICK:
            return
        state = self._engine.process_frame(frame)
        self._emit_state(state)
        if state.calibrated:
            self._active = False

    def _emit_state(self, state: CalibrationState | None = None) -> None:
        self.calibration_state_changed.emit(state or self._engine.state())
