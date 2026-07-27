"""Real CalibrationProvider backed by the manual click-calibration flow.

src.calibration.calibrate() opens its own native OpenCV window and reads
mouse/keyboard input in a blocking loop. OpenCV's HighGUI is not
thread-safe on all platforms (notably macOS, where window/UI calls must
happen on the main thread), so unlike CameraHandProvider this runs
calibrate() synchronously on the calling (Qt/main) thread rather than on a
worker QThread. The Qt window will not repaint while the OpenCV
calibration window is open -- a deliberate trade-off given that
constraint, not an oversight.
"""

from __future__ import annotations

import cv2

from src.calibration import calibrate
from src.gui.providers.base import CalibrationProvider
from src.models import CalibrationState


class ManualCalibrationProvider(CalibrationProvider):
    """Runs the click-4-corners calibration flow against a real camera."""

    def __init__(self, camera_index: int = 0, surface_size: tuple[int, int] = (1280, 720)) -> None:
        super().__init__()
        self._camera_index = camera_index
        self._surface_size = surface_size
        self.homography = None

    def start_calibration(self) -> None:
        """Open the camera and run the click-corner calibration flow.

        Blocks the calling thread until the user finishes or cancels
        ('q') calibration -- see module docstring for why.
        """
        self.calibration_state_changed.emit(
            CalibrationState(
                calibrated=False,
                in_progress=True,
                progress=0.0,
                transform_available=False,
                status_message="Calibrating... (click 4 corners in the camera window)",
            )
        )

        cap = cv2.VideoCapture(self._camera_index)
        try:
            surface_w, surface_h = self._surface_size
            self.homography = calibrate(cap, surface_w, surface_h)
        except SystemExit:
            self.calibration_state_changed.emit(
                CalibrationState(
                    calibrated=False,
                    in_progress=False,
                    progress=0.0,
                    transform_available=False,
                    status_message="Calibration cancelled",
                )
            )
            return
        finally:
            cap.release()

        self.calibration_state_changed.emit(
            CalibrationState(
                calibrated=True,
                in_progress=False,
                progress=1.0,
                transform_available=True,
                status_message="Calibration complete",
            )
        )
