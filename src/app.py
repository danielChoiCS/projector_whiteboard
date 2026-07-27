"""GUI entry point.

Wires MockHandProvider/MockCalibrationProvider into MainWindow by default.
Pass --camera to use the real camera-backed providers instead (requires a
working camera and the MediaPipe hand-landmarker model -- see
src/vision/hand_tracker.py).

Run from the project root as a module, e.g.:

    uv run python -m src.app
    uv run python -m src.app --camera

src/main.py remains the separate, non-GUI OpenCV whiteboard demo; this
file is the GUI's entry point.
"""

from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from src.gui.main_window import MainWindow
from src.gui.providers.mock import MockCalibrationProvider, MockHandProvider


def main() -> None:
    """Build and show MainWindow, then run the Qt event loop."""
    use_camera = "--camera" in sys.argv[1:]

    app = QApplication(sys.argv)

    if use_camera:
        from src.gui.providers.camera import CameraHandProvider
        from src.gui.providers.manual_calibration import ManualCalibrationProvider

        hand_provider = CameraHandProvider()
        calibration_provider = ManualCalibrationProvider()
    else:
        hand_provider = MockHandProvider()
        calibration_provider = MockCalibrationProvider()

    window = MainWindow(hand_provider, calibration_provider)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
