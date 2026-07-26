"""Overall application lifecycle state shared by gui and control."""

from enum import Enum


class SystemState(str, Enum):
    """High-level state of the whole application."""

    STARTING = "starting"
    CAMERA_UNAVAILABLE = "camera_unavailable"
    AWAITING_CALIBRATION = "awaiting_calibration"
    CALIBRATING = "calibrating"
    READY = "ready"
    TRACKING = "tracking"
    ERROR = "error"
