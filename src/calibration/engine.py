"""Mode-dispatching calibration engine.

Pure Python/OpenCV, with no PySide6 dependency: something that runs this on a
worker thread and forwards its CalibrationState over a Qt signal is a thin
adapter (see src/gui/providers), not part of this module.
"""

from __future__ import annotations

import numpy as np

from src.calibration.contour_detector import detect_contour_corners
from src.calibration.geometry import Point, compute_homography, order_corners
from src.calibration.red_sticker_detector import detect_red_sticker_corners
from src.models import CalibrationMode, CalibrationState, Matrix3x3


class CalibrationEngine:
    """Runs whichever corner-detection strategy is selected and tracks progress."""

    def __init__(self, mode: CalibrationMode = CalibrationMode.CONTOUR_DETECTION) -> None:
        self._mode = mode
        self._manual_points: list[Point] = []
        self._corners: list[Point] | None = None
        self._transform: np.ndarray | None = None

    @property
    def mode(self) -> CalibrationMode:
        """Currently selected corner-detection strategy."""
        return self._mode

    @property
    def corners(self) -> list[Point] | None:
        """The four detected corners, or None if not yet calibrated."""
        return self._corners

    @property
    def transform(self) -> np.ndarray | None:
        """Normalized camera-to-screen perspective transform, or None if uncalibrated."""
        return self._transform

    def set_mode(self, mode: CalibrationMode) -> None:
        """Switch strategy and discard any in-progress calibration attempt."""
        self._mode = mode
        self.reset()

    def reset(self) -> None:
        """Discard any collected points and the current calibration result."""
        self._manual_points = []
        self._corners = None
        self._transform = None

    def add_manual_point(self, x: float, y: float) -> CalibrationState:
        """Record one manually clicked corner. Ignored outside MANUAL_CLICK mode."""
        if self._mode == CalibrationMode.MANUAL_CLICK and len(self._manual_points) < 4:
            self._manual_points.append((x, y))
            if len(self._manual_points) == 4:
                self._finish(order_corners(self._manual_points))
        return self.state()

    def process_frame(self, frame: np.ndarray) -> CalibrationState:
        """Run the selected automatic detector against one camera frame."""
        if self._mode == CalibrationMode.RED_STICKER:
            found = detect_red_sticker_corners(frame)
        elif self._mode == CalibrationMode.CONTOUR_DETECTION:
            found = detect_contour_corners(frame)
        else:
            found = None

        if found is not None:
            frame_height, frame_width = frame.shape[:2]
            normalized = [(x / frame_width, y / frame_height) for x, y in found]
            self._finish(order_corners(normalized))
        return self.state()

    def _finish(self, corners: list[Point]) -> None:
        self._corners = corners
        self._transform = compute_homography(corners)

    def state(self) -> CalibrationState:
        """Build the CalibrationState reflecting the current mode and progress."""
        calibrated = self._corners is not None

        if self._mode == CalibrationMode.MANUAL_CLICK:
            progress = len(self._manual_points) / 4
            message = (
                "Calibration complete"
                if calibrated
                else f"Click corner {len(self._manual_points) + 1} of 4 on the camera view"
            )
        else:
            progress = 1.0 if calibrated else 0.0
            strategy_name = "red stickers" if self._mode == CalibrationMode.RED_STICKER else "board edges"
            message = "Calibration complete" if calibrated else f"Searching for {strategy_name}..."

        return CalibrationState(
            calibrated=calibrated,
            in_progress=not calibrated,
            progress=progress,
            transform_available=self._transform is not None,
            status_message=message,
            mode=self._mode,
            transform=_to_matrix(self._transform),
            corners=tuple(self._corners) if self._corners is not None else None,
        )


def _to_matrix(transform: np.ndarray | None) -> Matrix3x3 | None:
    if transform is None:
        return None
    return tuple(tuple(float(value) for value in row) for row in transform)
