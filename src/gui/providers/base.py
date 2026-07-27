"""Provider interfaces the GUI depends on instead of vision/calibration code.

Real implementations (owned by the vision and calibration teams) run their
processing on a worker QThread and emit these same signals; the GUI never
imports MediaPipe, OpenCV, or calibration algorithms directly.
"""

from PySide6.QtCore import QObject, Signal

from src.models import CalibrationMode, CalibrationState, HandState


class HandProvider(QObject):
    """Interface for anything that produces HandState updates.

    Subclasses must call ``start()``/``stop()`` to begin/end emitting
    ``hand_state_changed`` on their own thread of choice. Use
    ``request_stop()`` rather than ``stop()`` directly when calling from a
    different thread than the provider lives on (e.g. the GUI thread calling
    into a camera-backed provider on its worker thread) -- it's safe to call
    from anywhere, since the self-connected signal makes Qt queue the actual
    ``stop()`` onto the provider's own thread.
    """

    hand_state_changed = Signal(HandState)
    _stop_requested = Signal()

    def __init__(self) -> None:
        super().__init__()
        self._stop_requested.connect(self.stop)

    def start(self) -> None:
        """Begin producing hand state updates."""
        raise NotImplementedError

    def stop(self) -> None:
        """Stop producing hand state updates. Call on this provider's own thread."""
        raise NotImplementedError

    def request_stop(self) -> None:
        """Thread-safe: stop producing hand state updates, from any thread."""
        self._stop_requested.emit()


class CalibrationProvider(QObject):
    """Interface for anything that produces CalibrationState updates.

    ``start_calibration()`` is invoked by the GUI in response to user
    action (e.g. clicking "Start Calibration"). ``set_mode()`` and
    ``add_manual_point()`` are invoked in response to the calibration mode
    dropdown and clicks on the camera view, respectively.
    """

    calibration_state_changed = Signal(CalibrationState)

    def start_calibration(self) -> None:
        """(Re)start a calibration pass using the currently selected mode."""
        raise NotImplementedError

    def set_mode(self, mode: CalibrationMode) -> None:
        """Switch corner-detection strategy, discarding any current attempt."""
        raise NotImplementedError

    def add_manual_point(self, x: float, y: float) -> None:
        """Record one manually clicked corner. Ignored outside manual mode."""
        raise NotImplementedError
