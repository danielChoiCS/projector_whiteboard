import numpy as np

from src.calibration.contour_detector import detect_contour_corners

_CORNERS = np.array([[40, 40], [440, 40], [440, 320], [40, 320]], dtype=np.int32)


def _frame_with_board():
    import cv2

    frame = np.zeros((360, 480, 3), dtype=np.uint8)
    cv2.fillConvexPoly(frame, _CORNERS, (230, 230, 230))
    return frame


def test_detects_high_contrast_board_edge():
    frame = _frame_with_board()

    found = detect_contour_corners(frame)

    assert found is not None
    assert len(found) == 4
    for expected_x, expected_y in _CORNERS:
        assert any(
            abs(x - expected_x) < 5 and abs(y - expected_y) < 5 for x, y in found
        )


def test_returns_none_on_blank_frame():
    frame = np.zeros((360, 480, 3), dtype=np.uint8)

    assert detect_contour_corners(frame) is None
