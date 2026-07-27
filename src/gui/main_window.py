"""Main application window.

Wires provider signals to widget update slots and derives ApplicationState
from the latest hand/calibration states. This is the only place in the GUI
that performs cross-widget coordination; individual widgets stay dumb.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget

from src.gui.providers.base import CalibrationProvider, HandProvider
from src.gui.settings_persistence import (
    DEFAULT_SETTINGS_PATH,
    load_key_bindings,
    save_key_bindings,
)
from src.gui.widgets import (
    CalibrationPanel,
    CameraDevicePanel,
    CameraViewWidget,
    SettingsPanel,
    StatusPanel,
    TrackingPanel,
)
from src.models import (
    ApplicationState,
    CalibrationMode,
    CalibrationState,
    Gesture,
    HandState,
    KeyBindingConfig,
    SystemState,
)

_DEFAULT_CALIBRATION_MODE = CalibrationMode.CONTOUR_DETECTION

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
    """Top-level Project Whiteboard window.

    Does not call ``hand_provider.start()`` itself -- the caller (the
    composition root in main.py) starts it, since a camera-backed provider
    needs to be started on its own worker thread rather than this one.
    """

    camera_device_selected = Signal(object)  # int device index, or None for synthetic data

    def __init__(
        self,
        hand_provider: HandProvider,
        calibration_provider: CalibrationProvider,
        parent: QWidget | None = None,
        settings_path: Path = DEFAULT_SETTINGS_PATH,
        available_camera_devices: tuple[int, ...] = (),
        current_camera_device: int | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Project Whiteboard")

        self._hand_provider = hand_provider
        self._calibration_provider = calibration_provider
        self._latest_hand_state = _INITIAL_HAND_STATE
        self._latest_calibration_state = _INITIAL_CALIBRATION_STATE
        self._current_calibration_mode = _DEFAULT_CALIBRATION_MODE
        self._settings_path = settings_path
        self._key_binding_config = load_key_bindings(settings_path)
        self._camera_connected = False

        self._camera_view = CameraViewWidget()
        self._camera_device_panel = CameraDevicePanel(available_camera_devices, current_camera_device)
        self._calibration_panel = CalibrationPanel()
        self._tracking_panel = TrackingPanel()
        self._status_panel = StatusPanel()
        self._settings_panel = SettingsPanel(self._key_binding_config)

        left_column = QVBoxLayout()
        left_column.addWidget(self._camera_view)
        left_column.addWidget(self._camera_device_panel)
        left_column.addWidget(self._status_panel)

        right_column = QVBoxLayout()
        right_column.addWidget(self._calibration_panel)
        right_column.addWidget(self._tracking_panel)
        right_column.addWidget(self._settings_panel)
        right_column.addStretch()

        root_layout = QHBoxLayout(self)
        root_layout.addLayout(left_column, stretch=2)
        root_layout.addLayout(right_column, stretch=1)

        self._connect_providers()
        self._calibration_panel.start_calibration_requested.connect(
            self._camera_view.clear_markers
        )
        self._calibration_panel.mode_selected.connect(self._on_mode_selected)
        self._camera_view.corner_clicked.connect(self._on_corner_clicked)
        self._settings_panel.bindings_changed.connect(self._on_bindings_changed)
        self._camera_device_panel.device_selected.connect(self.camera_device_selected)

        self._refresh_status()

    def _connect_providers(self) -> None:
        # Dispatch to the provider via a genuine Qt connection (not a direct call)
        # so that, when the provider lives on a worker thread (the camera-backed
        # providers do), Qt auto-queues delivery instead of running it on this
        # (GUI) thread. The paired _on_* methods elsewhere only ever touch widgets.
        self._hand_provider.hand_state_changed.connect(self._on_hand_state)
        self._calibration_provider.calibration_state_changed.connect(self._on_calibration_state)
        self._calibration_panel.start_calibration_requested.connect(
            self._calibration_provider.start_calibration
        )
        self._calibration_panel.mode_selected.connect(self._calibration_provider.set_mode)
        self._camera_view.corner_clicked.connect(self._calibration_provider.add_manual_point)

    def _disconnect_providers(self) -> None:
        self._hand_provider.hand_state_changed.disconnect(self._on_hand_state)
        self._calibration_provider.calibration_state_changed.disconnect(self._on_calibration_state)
        self._calibration_panel.start_calibration_requested.disconnect(
            self._calibration_provider.start_calibration
        )
        self._calibration_panel.mode_selected.disconnect(self._calibration_provider.set_mode)
        self._camera_view.corner_clicked.disconnect(self._calibration_provider.add_manual_point)

    def set_providers(self, hand_provider: HandProvider, calibration_provider: CalibrationProvider) -> None:
        """Swap in new providers, e.g. when the user selects a different camera device.

        Does not start hand_provider -- same rule as construction time, the
        caller starts it on whichever thread is appropriate.
        """
        self._disconnect_providers()
        self._hand_provider = hand_provider
        self._calibration_provider = calibration_provider
        self._connect_providers()

        self._latest_hand_state = _INITIAL_HAND_STATE
        self._latest_calibration_state = _INITIAL_CALIBRATION_STATE
        self._camera_connected = False
        self._camera_view.clear_markers()
        self._tracking_panel.update_hand_state(_INITIAL_HAND_STATE)
        self._camera_view.update_hand_overlay(_INITIAL_HAND_STATE)
        self._calibration_panel.update_calibration(_INITIAL_CALIBRATION_STATE)
        self._camera_view.update_calibration_overlay(_INITIAL_CALIBRATION_STATE)
        self._camera_view.show_unavailable()
        self._refresh_status()

    @property
    def calibration_state(self) -> CalibrationState:
        """Most recently observed CalibrationState."""
        return self._latest_calibration_state

    @property
    def key_binding_config(self) -> KeyBindingConfig:
        """Currently configured gesture-to-input-action bindings."""
        return self._key_binding_config

    def _on_hand_state(self, state: HandState) -> None:
        self._latest_hand_state = state
        self._tracking_panel.update_hand_state(state)
        self._camera_view.update_hand_overlay(state)
        self._refresh_status()

    def _on_calibration_state(self, state: CalibrationState) -> None:
        self._latest_calibration_state = state
        self._calibration_panel.update_calibration(state)
        self._camera_view.update_calibration_overlay(state)
        self._refresh_status()

    def _on_mode_selected(self, mode: CalibrationMode) -> None:
        self._current_calibration_mode = mode
        self._camera_view.clear_markers()

    def _on_corner_clicked(self, x: float, y: float) -> None:
        if self._current_calibration_mode != CalibrationMode.MANUAL_CLICK:
            return
        if self._camera_view.marker_count < 4:
            self._camera_view.add_marker(x, y)

    def _on_bindings_changed(self, config: KeyBindingConfig) -> None:
        self._key_binding_config = config
        save_key_bindings(config, self._settings_path)

    def show_camera_frame(self, frame: np.ndarray) -> None:
        """Display one live camera frame in the camera preview."""
        self._camera_connected = True
        self._camera_view.show_frame(frame)
        self._refresh_status()

    def show_camera_unavailable(self, message: str = "Camera unavailable") -> None:
        """Revert the camera preview to its placeholder (e.g. camera disconnected)."""
        self._camera_connected = False
        self._camera_view.show_unavailable(message)
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
            camera_connected=self._camera_connected,
            tracking_active=hand.detected,
            calibrated=calibration.calibrated,
            message=message,
        )
        self._status_panel.update_application_state(application_state)
