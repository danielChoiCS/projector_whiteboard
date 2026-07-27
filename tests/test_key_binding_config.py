from src.models import Gesture, GestureBinding, InputAction, KeyBindingConfig


def test_default_bindings_cover_the_active_gestures():
    config = KeyBindingConfig()

    assert config.action_for(Gesture.MOVE).action == InputAction.MOUSE_MOVE
    # CLICK defaults to hold-to-drag, not a single click -- see
    # _default_bindings()'s docstring in key_binding_config.py.
    assert config.action_for(Gesture.CLICK).action == InputAction.MOUSE_DRAG


def test_default_bindings_have_no_entry_for_disabled_gestures():
    # DRAG/SCROLL classification is disabled for now -- only MOVE/CLICK ship
    # with a default binding.
    config = KeyBindingConfig()

    assert config.action_for(Gesture.DRAG) is None
    assert config.action_for(Gesture.SCROLL) is None


def test_action_for_returns_none_when_unbound():
    config = KeyBindingConfig(bindings=())

    assert config.action_for(Gesture.CLICK) is None


def test_custom_binding_with_key_press():
    binding = GestureBinding(Gesture.CLICK, InputAction.KEY_PRESS, key="space")
    config = KeyBindingConfig(bindings=(binding,))

    resolved = config.action_for(Gesture.CLICK)

    assert resolved.action == InputAction.KEY_PRESS
    assert resolved.key == "space"
