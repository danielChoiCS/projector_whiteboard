
from src.models import Gesture
from src.vision.gesture_classifier import classify_gesture, hand_position
from src.vision.landmarks import (
    INDEX_PIP,
    INDEX_TIP,
    MIDDLE_MCP,
    MIDDLE_PIP,
    MIDDLE_TIP,
    PINKY_PIP,
    PINKY_TIP,
    RING_PIP,
    RING_TIP,
    THUMB_TIP,
    WRIST,
)


def _landmarks(*, index=False, middle=False, ring=False, pinky=False, pinch=False):
    lm = [(0.5, 0.5, 0.0)] * 21
    lm[WRIST] = (0.5, 0.9, 0.0)
    lm[MIDDLE_MCP] = (0.5, 0.6, 0.0)

    def finger(pip_idx, tip_idx, x, extended):
        lm[pip_idx] = (x, 0.55, 0.0)
        lm[tip_idx] = (x, 0.35 if extended else 0.65, 0.0)

    finger(INDEX_PIP, INDEX_TIP, 0.45, index)
    finger(MIDDLE_PIP, MIDDLE_TIP, 0.50, middle)
    finger(RING_PIP, RING_TIP, 0.55, ring)
    finger(PINKY_PIP, PINKY_TIP, 0.60, pinky)

    lm[THUMB_TIP] = lm[INDEX_TIP] if pinch else (0.3, 0.7, 0.0)
    return lm


def test_open_hand_is_move():
    landmarks = _landmarks(index=True, middle=True, ring=True, pinky=True)
    assert classify_gesture(landmarks) == Gesture.MOVE


def test_fist_is_move_not_drag():
    # DRAG detection is disabled for now -- only MOVE/CLICK are supported.
    landmarks = _landmarks()
    assert classify_gesture(landmarks) == Gesture.MOVE


def test_index_and_middle_extended_is_move_not_scroll():
    # SCROLL detection is disabled for now -- only MOVE/CLICK are supported.
    landmarks = _landmarks(index=True, middle=True)
    assert classify_gesture(landmarks) == Gesture.MOVE


def test_pinch_is_click_even_with_fingers_extended():
    landmarks = _landmarks(index=True, middle=True, ring=True, pinky=True, pinch=True)
    assert classify_gesture(landmarks) == Gesture.CLICK


def test_hand_position_tracks_the_index_fingertip():
    landmarks = _landmarks(index=True)

    x, y = hand_position(landmarks)

    assert (x, y) == landmarks[INDEX_TIP][:2]


def test_hand_position_follows_index_fingertip_as_it_moves():
    extended = _landmarks(index=True)
    folded = _landmarks(index=False)

    assert hand_position(extended) != hand_position(folded)
