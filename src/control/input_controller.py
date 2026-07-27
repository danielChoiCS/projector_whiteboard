"""Converts recognized gestures into real mouse/keyboard input via PyAutoGUI.

No PySide6, vision, calibration, or gui dependency -- only src.models, plus
pyautogui itself. pyautogui is imported lazily (and injectable) so that
importing this module, and testing its dispatch logic, never requires a
real display/accessibility permissions or risks moving the real mouse.
"""

from __future__ import annotations

from typing import Any

from src.models import (
    CalibrationState,
    HandState,
    InputAction,
    KeyBindingConfig,
    Matrix3x3,
)

_SCROLL_STEP = 40
_DEFAULT_SMOOTHING = 0.4  # exponential moving average factor; lower = smoother but laggier


def _apply_homography(transform: Matrix3x3, x: float, y: float) -> tuple[float, float]:
    """Map one (x, y) point through a 3x3 perspective transform."""
    px = transform[0][0] * x + transform[0][1] * y + transform[0][2]
    py = transform[1][0] * x + transform[1][1] * y + transform[1][2]
    w = transform[2][0] * x + transform[2][1] * y + transform[2][2]
    if w == 0:
        return (0.0, 0.0)
    return (px / w, py / w)


class InputController:
    """Maps HandState + CalibrationState + KeyBindingConfig to OS input.

    Stateful across dispatch() calls: clicks and key presses fire once per
    gesture activation (edge-triggered), while drag and scroll continue for
    as long as the gesture is held (level-triggered). The mapped screen
    position is also smoothed (exponential moving average) across calls to
    damp frame-to-frame hand-tracking jitter before it reaches the cursor.
    """

    def __init__(self, pyautogui_module: Any = None, smoothing: float = _DEFAULT_SMOOTHING) -> None:
        if pyautogui_module is None:
            import pyautogui as pyautogui_module
        self._pyautogui = pyautogui_module
        self._pyautogui.FAILSAFE = True
        # PyAutoGUI sleeps for PAUSE seconds (0.1 by default) after every
        # single call, including moveTo() -- since dispatch() runs on the
        # same worker thread as camera capture and MediaPipe inference, that
        # sleep was blocking the whole pipeline to ~10 fps regardless of how
        # fast the camera/model could actually run.
        self._pyautogui.PAUSE = 0
        self._screen_width, self._screen_height = self._pyautogui.size()
        self._active_action: InputAction | None = None
        self._smoothing = smoothing
        self._smoothed_position: tuple[float, float] | None = None

    def dispatch(
        self, hand: HandState, calibration: CalibrationState, bindings: KeyBindingConfig
    ) -> None:
        """Perform (at most) one OS input action for the current hand state."""
        if not hand.detected or calibration.transform is None:
            self._release_held_action()
            self._smoothed_position = None
            return

        binding = bindings.action_for(hand.gesture)
        action = binding.action if binding else InputAction.NONE
        screen_x, screen_y = self._map_to_screen(hand.x, hand.y, calibration.transform)

        if action == InputAction.MOUSE_MOVE:
            self._release_held_action()
            self._pyautogui.moveTo(screen_x, screen_y)
        elif action == InputAction.MOUSE_LEFT_CLICK:
            self._fire_once(action, lambda: self._pyautogui.click(x=screen_x, y=screen_y, button="left"))
        elif action == InputAction.MOUSE_RIGHT_CLICK:
            self._fire_once(action, lambda: self._pyautogui.click(x=screen_x, y=screen_y, button="right"))
        elif action == InputAction.MOUSE_DRAG:
            self._hold_drag(screen_x, screen_y)
        elif action in (InputAction.SCROLL_UP, InputAction.SCROLL_DOWN):
            self._release_held_action()
            self._pyautogui.scroll(_SCROLL_STEP if action == InputAction.SCROLL_UP else -_SCROLL_STEP)
        elif action == InputAction.KEY_PRESS and binding is not None and binding.key:
            self._fire_once(action, lambda: self._pyautogui.press(binding.key))
        else:
            self._release_held_action()

    def _fire_once(self, action: InputAction, fire) -> None:
        if self._active_action != action:
            fire()
        self._active_action = action

    def _hold_drag(self, screen_x: int, screen_y: int) -> None:
        if self._active_action != InputAction.MOUSE_DRAG:
            self._pyautogui.mouseDown(x=screen_x, y=screen_y)
            self._active_action = InputAction.MOUSE_DRAG
        else:
            self._pyautogui.moveTo(screen_x, screen_y)

    def _release_held_action(self) -> None:
        if self._active_action == InputAction.MOUSE_DRAG:
            self._pyautogui.mouseUp()
        self._active_action = None

    def _map_to_screen(self, x: float, y: float, transform: Matrix3x3) -> tuple[int, int]:
        norm_x, norm_y = _apply_homography(transform, x, y)
        clamped_x = min(max(norm_x, 0.0), 1.0)
        clamped_y = min(max(norm_y, 0.0), 1.0)
        raw = (clamped_x * self._screen_width, clamped_y * self._screen_height)
        smoothed_x, smoothed_y = self._smooth(raw)
        return (int(smoothed_x), int(smoothed_y))

    def _smooth(self, point: tuple[float, float]) -> tuple[float, float]:
        """Exponential moving average over screen-space targets, to damp
        frame-to-frame landmark jitter before it reaches the real cursor."""
        if self._smoothed_position is None:
            self._smoothed_position = point
        else:
            prev_x, prev_y = self._smoothed_position
            self._smoothed_position = (
                self._smoothing * point[0] + (1 - self._smoothing) * prev_x,
                self._smoothing * point[1] + (1 - self._smoothing) * prev_y,
            )
        return self._smoothed_position
