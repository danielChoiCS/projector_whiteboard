"""Calibration data model, produced by the calibration subsystem."""

from dataclasses import dataclass


@dataclass(frozen=True)
class CalibrationState:
    """Snapshot of whiteboard calibration progress and result.

    Attributes:
        calibrated: Whether a valid camera-to-screen transform exists.
        in_progress: Whether a calibration pass is currently running.
        progress: Calibration completion in [0.0, 1.0]. Meaningless when
            ``in_progress`` is False and ``calibrated`` is False.
        transform_available: Whether a coordinate transform is ready for
            the control subsystem to consume.
        status_message: Human-readable status text for display in the GUI.
    """

    calibrated: bool
    in_progress: bool
    progress: float
    transform_available: bool
    status_message: str
