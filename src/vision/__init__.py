"""Vision subsystem: camera-frame hand tracking and gesture debouncing.

Framework-independent by design (only cv2/numpy/mediapipe) so hand_tracker.py
and gestures.py stay runnable standalone, outside the GUI. src.models.Gesture
conversion happens at the GUI provider boundary, not in here.
"""

from src.vision.gestures import GestureController
from src.vision.hand_tracker import HandTracker, get_hand_state

__all__ = [
    "GestureController",
    "HandTracker",
    "get_hand_state",
]
