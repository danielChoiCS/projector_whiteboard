"""Gesture vocabulary shared by vision, control, and gui."""

from enum import Enum


class Gesture(str, Enum):
    """Recognized hand gesture states.

    Inherits from ``str`` so values compare and serialize as plain strings
    (e.g. ``Gesture.MOVE == "move"``) while remaining a typed enum.
    """

    NONE = "none"
    MOVE = "move"
    CLICK = "click"
    DRAG = "drag"
    SCROLL = "scroll"
