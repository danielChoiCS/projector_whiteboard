"""Main application window.

Wires provider signals to widget update slots and derives ApplicationState
from the latest hand/calibration states. This is the only place in the GUI
that performs cross-widget coordination; individual widgets stay dumb.
"""

from __future__ import annotations

from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget

from src.gui.providers.base import CalibrationProvider, HandProvider
from src.gui.widgets import (
    CalibrationPanel,
    CameraViewWidget,
    StatusPanel,
    TrackingPanel,
)
from src.models import (
    ApplicationState,
    CalibrationState,
    Gesture,
    HandState,
    SystemState,
)

_INITIAL_HAND_STATE = HandState(
    detected=False, x=0.0, y=0.0, gesture=Gesture.NONE, confidence=0.0, timestamp=0.0
)
_INITIAL_CALIBRATION_STATE = CalibrationState(
    calibrated=False,
    in_progress=False,
    progress=0.0,
    transform_available=False,
    status_message="Not calibrated",
)


class MainWindow(QWidget):
    """Top-level Project Whiteboard window."""

    def __init__(
        self,
        hand_provider: HandProvider,
        calibration_provider: CalibrationProvider,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Project Whiteboard")

        self._hand_provider = hand_provider
        self._calibration_provider = calibration_provider
        self._latest_hand_state = _INITIAL_HAND_STATE
        self._latest_calibration_state = _INITIAL_CALIBRATION_STATE

        self._camera_view = CameraViewWidget()
        self._calibration_panel = CalibrationPanel()
        self._tracking_panel = TrackingPanel()
        self._status_panel = StatusPanel()

        left_column = QVBoxLayout()
        left_column.addWidget(self._camera_view)
        left_column.addWidget(self._status_panel)

        right_column = QVBoxLayout()
        right_column.addWidget(self._calibration_panel)
        right_column.addWidget(self._tracking_panel)
        right_column.addStretch()

        root_layout = QHBoxLayout(self)
        root_layout.addLayout(left_column, stretch=2)
        root_layout.addLayout(right_column, stretch=1)

        self._hand_provider.hand_state_changed.connect(self._on_hand_state)
        self._calibration_provider.calibration_state_changed.connect(
            self._on_calibration_state
        )
        self._calibration_panel.start_calibration_requested.connect(
            self._calibration_provider.start_calibration
        )

        self._refresh_status()
        self._hand_provider.start()

    def _on_hand_state(self, state: HandState) -> None:
        self._latest_hand_state = state
        self._tracking_panel.update_hand_state(state)
        self._refresh_status()

    def _on_calibration_state(self, state: CalibrationState) -> None:
        self._latest_calibration_state = state
        self._calibration_panel.update_calibration(state)
        self._refresh_status()

    def _refresh_status(self) -> None:
        hand = self._latest_hand_state
        calibration = self._latest_calibration_state

        if calibration.in_progress:
            system_state = SystemState.CALIBRATING
            message = calibration.status_message
        elif not calibration.calibrated:
            system_state = SystemState.AWAITING_CALIBRATION
            message = "Calibration required before tracking can begin."
        elif hand.detected:
            system_state = SystemState.TRACKING
            message = f"Tracking hand, gesture={hand.gesture.value}"
        else:
            system_state = SystemState.READY
            message = "Calibrated. Waiting for hand."

        application_state = ApplicationState(
            system_state=system_state,
            camera_connected=False,
            tracking_active=hand.detected,
            calibrated=calibration.calibrated,
            message=message,
        )
        self._status_panel.update_application_state(application_state)
