import cv2
import numpy as np

from src.gui.providers.camera_calibration_provider import CameraCalibrationProvider
from src.models import CalibrationMode


def test_frames_ignored_until_calibration_started():
    provider = CameraCalibrationProvider()
    received = []
    provider.calibration_state_changed.connect(received.append)

    provider.process_frame(np.zeros((360, 480, 3), dtype=np.uint8))

    assert received == []


def test_calibrates_from_frames_once_active():
    provider = CameraCalibrationProvider()
    provider.set_mode(CalibrationMode.RED_STICKER)
    provider.start_calibration()
    received = []
    provider.calibration_state_changed.connect(received.append)

    frame = np.zeros((360, 480, 3), dtype=np.uint8)
    for x, y in [(40, 40), (440, 40), (440, 320), (40, 320)]:
        cv2.circle(frame, (x, y), 8, (0, 0, 255), -1)
    provider.process_frame(frame)

    assert received[-1].calibrated
    assert received[-1].transform is not None


def test_stops_processing_frames_once_calibrated():
    provider = CameraCalibrationProvider()
    provider.set_mode(CalibrationMode.RED_STICKER)
    provider.start_calibration()

    frame = np.zeros((360, 480, 3), dtype=np.uint8)
    for x, y in [(40, 40), (440, 40), (440, 320), (40, 320)]:
        cv2.circle(frame, (x, y), 8, (0, 0, 255), -1)
    provider.process_frame(frame)

    received = []
    provider.calibration_state_changed.connect(received.append)
    provider.process_frame(frame)

    assert received == []


def test_manual_mode_ignores_frames_entirely():
    provider = CameraCalibrationProvider()
    provider.set_mode(CalibrationMode.MANUAL_CLICK)
    provider.start_calibration()
    received = []
    provider.calibration_state_changed.connect(received.append)

    provider.process_frame(np.zeros((360, 480, 3), dtype=np.uint8))

    assert received == []


def test_set_mode_deactivates_current_attempt():
    provider = CameraCalibrationProvider()
    provider.set_mode(CalibrationMode.RED_STICKER)
    provider.start_calibration()

    provider.set_mode(CalibrationMode.CONTOUR_DETECTION)

    received = []
    provider.calibration_state_changed.connect(received.append)
    provider.process_frame(np.zeros((360, 480, 3), dtype=np.uint8))

    assert received == []
