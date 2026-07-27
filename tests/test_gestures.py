from src.vision.gestures import GestureController


def test_first_gesture_after_none_triggers_immediately():
    ctrl = GestureController(cooldown_frames=15)
    is_new, gesture = ctrl.update("point")
    assert is_new is True
    assert gesture == "point"


def test_holding_the_same_gesture_does_not_retrigger():
    ctrl = GestureController(cooldown_frames=15)
    ctrl.update("point")
    is_new, gesture = ctrl.update("point")
    assert is_new is False
    assert gesture == "point"


def test_switching_gesture_during_cooldown_does_not_trigger():
    ctrl = GestureController(cooldown_frames=15)
    ctrl.update("point")   # triggers, starts cooldown
    ctrl.update(None)      # gesture drops
    is_new, gesture = ctrl.update("fist")
    assert is_new is False
    assert gesture == "fist"


def test_switching_gesture_after_cooldown_elapses_triggers_again():
    ctrl = GestureController(cooldown_frames=2)
    ctrl.update("point")   # triggers, cooldown = 2
    ctrl.update(None)      # cooldown -> 1
    ctrl.update(None)      # cooldown -> 0
    is_new, gesture = ctrl.update("fist")
    assert is_new is True
    assert gesture == "fist"


def test_gesture_passes_through_unchanged_every_frame_while_held():
    ctrl = GestureController(cooldown_frames=15)
    ctrl.update("fist")
    _, gesture = ctrl.update("fist")
    assert gesture == "fist"


def test_reset_clears_active_gesture_and_cooldown():
    ctrl = GestureController(cooldown_frames=15)
    ctrl.update("point")
    ctrl.reset()
    is_new, gesture = ctrl.update("point")
    assert is_new is True
    assert gesture == "point"
