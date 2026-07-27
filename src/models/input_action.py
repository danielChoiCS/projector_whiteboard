"""OS-level input actions a gesture can be bound to."""

from enum import Enum


class InputAction(str, Enum):
    """An action the input controller can perform in response to a gesture."""

    NONE = "none"
    MOUSE_MOVE = "mouse_move"
    MOUSE_LEFT_CLICK = "mouse_left_click"
    MOUSE_RIGHT_CLICK = "mouse_right_click"
    MOUSE_DRAG = "mouse_drag"
    SCROLL_UP = "scroll_up"
    SCROLL_DOWN = "scroll_down"
    KEY_PRESS = "key_press"
