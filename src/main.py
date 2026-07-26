"""Entry point for Project Whiteboard.

Wires mock vision/calibration providers into the GUI so it runs before the
real subsystems exist. Swapping in real providers later is a change to this
file only; src/gui and src/models are unaffected.
"""

import sys

from PySide6.QtWidgets import QApplication

from src.gui.main_window import MainWindow
from src.gui.providers.mock import MockCalibrationProvider, MockHandProvider


def main() -> None:
    """Launch the Project Whiteboard GUI."""
    app = QApplication(sys.argv)

    hand_provider = MockHandProvider()
    calibration_provider = MockCalibrationProvider()

    window = MainWindow(hand_provider, calibration_provider)
    window.resize(720, 480)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
