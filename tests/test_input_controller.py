from src.control.input_controller import InputController, _apply_homography
from src.models import (
    CalibrationState,
    Gesture,
    GestureBinding,
    HandState,
    InputAction,
    KeyBindingConfig,
)

_IDENTITY = ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))


class _FakePyAutoGUI:
    def __init__(self, screen_size=(1000, 500)):
        self._screen_size = screen_size
        self.calls = []
        self.FAILSAFE = None
        self.PAUSE = None

    def size(self):
        return self._screen_size

    def moveTo(self, x, y):
        self.calls.append(("moveTo", x, y))

    def click(self, x, y, button):
        self.calls.append(("click", x, y, button))

    def mouseDown(self, x, y):
        self.calls.append(("mouseDown", x, y))

    def mouseUp(self):
        self.calls.append(("mouseUp",))

    def scroll(self, amount):
        self.calls.append(("scroll", amount))

    def press(self, key):
        self.calls.append(("press", key))


def _hand(gesture, *, detected=True, x=0.5, y=0.5):
    return HandState(detected=detected, x=x, y=y, gesture=gesture, confidence=1.0, timestamp=0.0)


def _calibration(transform=_IDENTITY):
    return CalibrationState(
        calibrated=transform is not None,
        in_progress=False,
        progress=1.0 if transform else 0.0,
        transform_available=transform is not None,
        status_message="",
        transform=transform,
    )


def test_apply_homography_identity_transform_is_unchanged():
    assert _apply_homography(_IDENTITY, 0.3, 0.7) == (0.3, 0.7)


def test_disables_pyautogui_auto_pause():
    # pyautogui.PAUSE defaults to 0.1s and sleeps after every single call --
    # since dispatch() runs on the camera/inference worker thread, that would
    # otherwise cap the whole pipeline to ~10 fps.
    fake = _FakePyAutoGUI()

    InputController(pyautogui_module=fake)

    assert fake.PAUSE == 0


def test_no_hand_detected_dispatches_nothing():
    fake = _FakePyAutoGUI()
    controller = InputController(pyautogui_module=fake)

    controller.dispatch(_hand(Gesture.MOVE, detected=False), _calibration(), KeyBindingConfig())

    assert fake.calls == []


def test_uncalibrated_dispatches_nothing():
    fake = _FakePyAutoGUI()
    controller = InputController(pyautogui_module=fake)

    controller.dispatch(_hand(Gesture.MOVE), _calibration(transform=None), KeyBindingConfig())

    assert fake.calls == []


def test_move_gesture_moves_mouse_to_mapped_screen_position():
    fake = _FakePyAutoGUI(screen_size=(1000, 500))
    controller = InputController(pyautogui_module=fake)

    controller.dispatch(_hand(Gesture.MOVE, x=0.5, y=0.5), _calibration(), KeyBindingConfig())

    assert fake.calls == [("moveTo", 500, 250)]


def test_move_snaps_on_first_sample_then_smooths_subsequent_ones():
    fake = _FakePyAutoGUI(screen_size=(1000, 500))
    controller = InputController(pyautogui_module=fake, smoothing=0.5)
    bindings = KeyBindingConfig()

    controller.dispatch(_hand(Gesture.MOVE, x=0.0, y=0.5), _calibration(), bindings)
    controller.dispatch(_hand(Gesture.MOVE, x=1.0, y=0.5), _calibration(), bindings)

    assert fake.calls[0] == ("moveTo", 0, 250)  # no lag on the very first sample
    assert fake.calls[1] == ("moveTo", 500, 250)  # halfway toward the new target, not there yet


def test_smoothing_resets_after_hand_is_lost():
    fake = _FakePyAutoGUI(screen_size=(1000, 500))
    controller = InputController(pyautogui_module=fake, smoothing=0.5)
    bindings = KeyBindingConfig()

    controller.dispatch(_hand(Gesture.MOVE, x=0.0, y=0.5), _calibration(), bindings)
    controller.dispatch(_hand(Gesture.MOVE, detected=False), _calibration(), bindings)
    controller.dispatch(_hand(Gesture.MOVE, x=1.0, y=0.5), _calibration(), bindings)

    # snaps directly to the new target instead of smoothing from the stale
    # pre-gap position, which would otherwise drag the cursor across the
    # screen when a hand reappears somewhere completely different
    assert fake.calls[-1] == ("moveTo", 1000, 250)


def test_click_gesture_defaults_to_hold_and_drag():
    # CLICK's default binding is MOUSE_DRAG, not a single click -- so the
    # cursor keeps following the pinch position while it's held (a brief
    # pinch-and-release still behaves like an ordinary click: mouseDown
    # immediately followed by mouseUp). See KeyBindingConfig's
    # _default_bindings() docstring for why.
    fake = _FakePyAutoGUI()
    controller = InputController(pyautogui_module=fake)
    bindings = KeyBindingConfig()

    controller.dispatch(_hand(Gesture.CLICK), _calibration(), bindings)
    controller.dispatch(_hand(Gesture.CLICK), _calibration(), bindings)

    assert fake.calls[0][0] == "mouseDown"
    assert fake.calls[1][0] == "moveTo"

    controller.dispatch(_hand(Gesture.MOVE), _calibration(), bindings)

    assert fake.calls[-2][0] == "mouseUp"
    assert fake.calls[-1][0] == "moveTo"


def test_explicit_left_click_binding_still_fires_once_per_activation():
    # MOUSE_LEFT_CLICK (a single, non-moving click) is still fully supported
    # -- just no longer CLICK's default -- for anyone who explicitly wants it.
    fake = _FakePyAutoGUI()
    controller = InputController(pyautogui_module=fake)
    bindings = KeyBindingConfig(
        bindings=(GestureBinding(Gesture.CLICK, InputAction.MOUSE_LEFT_CLICK),)
    )

    controller.dispatch(_hand(Gesture.CLICK), _calibration(), bindings)
    controller.dispatch(_hand(Gesture.CLICK), _calibration(), bindings)

    assert len([c for c in fake.calls if c[0] == "click"]) == 1

    controller.dispatch(_hand(Gesture.MOVE, x=0.9, y=0.9), _calibration(), bindings)
    controller.dispatch(_hand(Gesture.CLICK), _calibration(), bindings)

    assert len([c for c in fake.calls if c[0] == "click"]) == 2


def test_drag_gesture_holds_mouse_down_then_releases_on_change():
    # DRAG has no default binding anymore (only MOVE/CLICK are supported by
    # default), but InputController's action-dispatch logic is still generic
    # -- explicitly bind it here to verify that logic still works.
    fake = _FakePyAutoGUI()
    controller = InputController(pyautogui_module=fake)
    bindings = KeyBindingConfig(bindings=(GestureBinding(Gesture.DRAG, InputAction.MOUSE_DRAG),))

    controller.dispatch(_hand(Gesture.DRAG), _calibration(), bindings)
    controller.dispatch(_hand(Gesture.DRAG), _calibration(), bindings)

    assert fake.calls[0][0] == "mouseDown"
    assert fake.calls[1][0] == "moveTo"

    controller.dispatch(_hand(Gesture.MOVE), _calibration(), bindings)

    assert fake.calls[-1][0] == "mouseUp"


def test_scroll_gesture_repeats_every_dispatch():
    # SCROLL has no default binding anymore -- see test_drag_gesture above.
    fake = _FakePyAutoGUI()
    controller = InputController(pyautogui_module=fake)
    bindings = KeyBindingConfig(bindings=(GestureBinding(Gesture.SCROLL, InputAction.SCROLL_DOWN),))

    controller.dispatch(_hand(Gesture.SCROLL), _calibration(), bindings)
    controller.dispatch(_hand(Gesture.SCROLL), _calibration(), bindings)

    assert fake.calls == [("scroll", -40), ("scroll", -40)]


def test_key_press_binding_fires_once_per_activation():
    fake = _FakePyAutoGUI()
    controller = InputController(pyautogui_module=fake)
    bindings = KeyBindingConfig(
        bindings=(GestureBinding(Gesture.CLICK, InputAction.KEY_PRESS, key="space"),)
    )

    controller.dispatch(_hand(Gesture.CLICK), _calibration(), bindings)
    controller.dispatch(_hand(Gesture.CLICK), _calibration(), bindings)

    assert fake.calls == [("press", "space")]
