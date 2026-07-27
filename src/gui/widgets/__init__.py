"""GUI widgets. Each widget only consumes models and exposes update slots."""

from src.gui.widgets.calibration_panel import CalibrationPanel
from src.gui.widgets.camera_device_panel import CameraDevicePanel
from src.gui.widgets.camera_view import CameraViewWidget
from src.gui.widgets.settings_panel import SettingsPanel
from src.gui.widgets.status_panel import StatusPanel
from src.gui.widgets.tracking_panel import TrackingPanel

__all__ = [
    "CalibrationPanel",
    "CameraDevicePanel",
    "CameraViewWidget",
    "SettingsPanel",
    "StatusPanel",
    "TrackingPanel",
]
