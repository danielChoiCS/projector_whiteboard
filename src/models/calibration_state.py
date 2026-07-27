"""Calibration data model, produced by the calibration subsystem."""

from __future__ import annotations

from dataclasses import dataclass

from src.models.calibration_mode import CalibrationMode

# A 3x3 perspective transform matrix, row-major. Plain nested tuples (rather
# than a numpy array) keep this model free of a numpy dependency and hashable.
Matrix3x3 = tuple[
    tuple[float, float, float], tuple[float, float, float], tuple[float, float, float]
]

Point = tuple[float, float]


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
        mode: Corner-detection strategy currently selected.
        transform: The camera-to-output perspective transform, once
            calibrated. This is the control subsystem's only route to the
            transform -- it must not import src.calibration directly.
        corners: The four detected corners, normalized [0, 1] and ordered
            (top-left, top-right, bottom-right, bottom-left), once
            calibrated. For GUI overlay display only.
    """

    calibrated: bool
    in_progress: bool
    progress: float
    transform_available: bool
    status_message: str
    mode: CalibrationMode = CalibrationMode.CONTOUR_DETECTION
    transform: Matrix3x3 | None = None
    corners: tuple[Point, Point, Point, Point] | None = None
