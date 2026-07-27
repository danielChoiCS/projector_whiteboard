"""Hand tracking and gesture recognition. Only depends on src.models.

hand_tracker.py lazily imports mediapipe/cv2-heavy code so that
gesture_classifier's pure geometry can be used and tested independently.
"""

from src.vision.gesture_classifier import classify_gesture, hand_position

__all__ = [
    "classify_gesture",
    "hand_position",
]
