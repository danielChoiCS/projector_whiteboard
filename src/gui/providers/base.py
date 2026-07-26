"""Provider interfaces the GUI depends on instead of vision/calibration code.

Real implementations (owned by the vision and calibration teams) run their
processing on a worker QThread and emit these same signals; the GUI never
imports MediaPipe, OpenCV, or calibration algorithms directly.
"""

from PySide6.QtCore import QObject, Signal

from src.models import CalibrationState, HandState


class HandProvider(QObject):
    """Interface for anything that produces HandState updates.

    Subclasses must call ``start()``/``stop()`` to begin/end emitting
    ``hand_state_changed`` on their own thread of choice.
    """

    hand_state_changed = Signal(HandState)

    def start(self) -> None:
        """Begin producing hand state updates."""
        raise NotImplementedError

    def stop(self) -> None:
        """Stop producing hand state updates."""
        raise NotImplementedError


class CalibrationProvider(QObject):
    """Interface for anything that produces CalibrationState updates.

    ``start_calibration()`` is invoked by the GUI in response to user
    action (e.g. clicking "Start Calibration").
    """

    calibration_state_changed = Signal(CalibrationState)

    def start_calibration(self) -> None:
        """Begin a calibration pass."""
        raise NotImplementedError
