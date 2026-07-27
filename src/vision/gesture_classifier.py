"""Pure geometric gesture classification from hand landmarks.

No MediaPipe, camera, or PySide6 dependency: given a set of 21 hand
landmarks in MediaPipe's normalized coordinate convention, this module
decides which Gesture they represent. Kept separate from hand_tracker.py so
it can be unit-tested against synthetic landmark data.
"""

from __future__ import annotations

import math

from src.models import Gesture
from src.vision.landmarks import INDEX_TIP, THUMB_TIP, HandLandmarks

Point = tuple[float, float]

_PINCH_DISTANCE_THRESHOLD = 0.06


def _distance_xy(a: tuple[float, float, float], b: tuple[float, float, float]) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def _is_pinching(landmarks: HandLandmarks) -> bool:
    return _distance_xy(landmarks[THUMB_TIP], landmarks[INDEX_TIP]) < _PINCH_DISTANCE_THRESHOLD


def classify_gesture(landmarks: HandLandmarks) -> Gesture:
    """Classify one frame's hand landmarks into a Gesture.

    Only MOVE and CLICK are supported for now -- Gesture.DRAG/SCROLL and
    their detection logic (fist / two-finger extended) are deliberately
    disabled rather than removed, to simplify the initial gesture set. Any
    non-pinch hand pose is treated as MOVE.
    """
    if _is_pinching(landmarks):
        return Gesture.CLICK
    return Gesture.MOVE


def hand_position(landmarks: HandLandmarks) -> Point:
    """Return the normalized (x, y) position representing the cursor target.

    Uses the index fingertip, so the cursor tracks where the user is
    pointing -- the natural interpretation of a pointing gesture.
    """
    index_tip = landmarks[INDEX_TIP]
    return (index_tip[0], index_tip[1])
