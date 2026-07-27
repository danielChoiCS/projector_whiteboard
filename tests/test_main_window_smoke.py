import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from src.gui.main_window import MainWindow
from src.gui.providers.mock import MockCalibrationProvider, MockHandProvider


def test_main_window_constructs_and_starts_uncalibrated():
    app = QApplication.instance() or QApplication([])
    hand_provider = MockHandProvider()
    calibration_provider = MockCalibrationProvider()

    window = MainWindow(hand_provider, calibration_provider)

    assert window._latest_hand_state.detected is False
    assert window._latest_calibration_state.calibrated is False

    hand_provider.stop()
    _ = app
