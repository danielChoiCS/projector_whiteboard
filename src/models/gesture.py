"""Gesture vocabulary shared by vision, control, and gui.

Values match src.vision.hand_tracker's raw gesture strings exactly
("point"/"fist"/"open") so a HandProvider can convert a hand_tracker.py
result with a plain ``Gesture(raw_state["gesture"])`` call, and
NONE covers the "no hand detected" case hand_tracker.py represents as
``None`` instead of a gesture string.
"""

from enum import Enum


class Gesture(str, Enum):
    """Recognized hand gesture states.

    Inherits from ``str`` so values compare and serialize as plain strings
    (e.g. ``Gesture.POINT == "point"``) while remaining a typed enum.
    """

    NONE = "none"    # no hand detected
    OPEN = "open"     # relaxed/open hand -- hover, no action
    POINT = "point"   # index finger extended -- draw
    FIST = "fist"     # closed fist -- erase
