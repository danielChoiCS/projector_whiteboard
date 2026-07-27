import cv2
import numpy as np

from src.calibration.engine import CalibrationEngine
from src.models import CalibrationMode


def test_manual_mode_calibrates_after_four_points():
    engine = CalibrationEngine(mode=CalibrationMode.MANUAL_CLICK)

    for point in [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0)]:
        state = engine.add_manual_point(*point)
        assert not state.calibrated

    state = engine.add_manual_point(0.0, 1.0)

    assert state.calibrated
    assert state.transform_available
    assert engine.transform.shape == (3, 3)


def test_manual_mode_ignores_extra_points_past_four():
    engine = CalibrationEngine(mode=CalibrationMode.MANUAL_CLICK)
    for point in [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]:
        engine.add_manual_point(*point)

    engine.add_manual_point(5.0, 5.0)

    assert engine.corners is not None
    assert len(engine.corners) == 4


def test_red_sticker_mode_calibrates_from_frame():
    engine = CalibrationEngine(mode=CalibrationMode.RED_STICKER)
    frame = np.zeros((360, 480, 3), dtype=np.uint8)
    for x, y in [(40, 40), (440, 40), (440, 320), (40, 320)]:
        cv2.circle(frame, (x, y), 8, (0, 0, 255), -1)

    state = engine.process_frame(frame)

    assert state.calibrated
    assert state.mode == CalibrationMode.RED_STICKER


def test_contour_mode_reports_not_calibrated_on_blank_frame():
    engine = CalibrationEngine(mode=CalibrationMode.CONTOUR_DETECTION)
    frame = np.zeros((360, 480, 3), dtype=np.uint8)

    state = engine.process_frame(frame)

    assert not state.calibrated
    assert state.in_progress


def test_set_mode_resets_progress():
    engine = CalibrationEngine(mode=CalibrationMode.MANUAL_CLICK)
    engine.add_manual_point(0.0, 0.0)

    engine.set_mode(CalibrationMode.CONTOUR_DETECTION)

    assert engine.corners is None
    state = engine.state()
    assert not state.calibrated
    assert state.mode == CalibrationMode.CONTOUR_DETECTION
