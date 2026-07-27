import cv2
import numpy as np

from src.calibration.red_sticker_detector import detect_red_sticker_corners

_CORNERS = [(40, 40), (440, 40), (440, 320), (40, 320)]


def _frame_with_stickers(corners):
    frame = np.zeros((360, 480, 3), dtype=np.uint8)
    for x, y in corners:
        cv2.circle(frame, (x, y), 8, (0, 0, 255), -1)
    return frame


def test_detects_four_red_stickers():
    frame = _frame_with_stickers(_CORNERS)

    found = detect_red_sticker_corners(frame)

    assert found is not None
    assert len(found) == 4
    for expected_x, expected_y in _CORNERS:
        assert any(
            abs(x - expected_x) < 3 and abs(y - expected_y) < 3 for x, y in found
        )


def test_returns_none_with_fewer_than_four_stickers():
    frame = _frame_with_stickers(_CORNERS[:3])

    assert detect_red_sticker_corners(frame) is None


def test_ignores_non_red_blobs():
    frame = np.zeros((360, 480, 3), dtype=np.uint8)
    cv2.circle(frame, (100, 100), 8, (255, 0, 0), -1)

    assert detect_red_sticker_corners(frame) is None
