from src.gui.settings_persistence import load_key_bindings, save_key_bindings
from src.models import Gesture, GestureBinding, InputAction, KeyBindingConfig


def test_load_returns_defaults_when_file_missing(tmp_path):
    config = load_key_bindings(tmp_path / "does_not_exist.json")

    assert config == KeyBindingConfig()


def test_save_then_load_round_trips(tmp_path):
    path = tmp_path / "settings.json"
    original = KeyBindingConfig(
        bindings=(
            GestureBinding(Gesture.MOVE, InputAction.MOUSE_MOVE),
            GestureBinding(Gesture.CLICK, InputAction.KEY_PRESS, key="space"),
        )
    )

    save_key_bindings(original, path)
    loaded = load_key_bindings(path)

    assert loaded == original


def test_save_creates_parent_directories(tmp_path):
    path = tmp_path / "nested" / "dir" / "settings.json"

    save_key_bindings(KeyBindingConfig(), path)

    assert path.exists()


def test_load_returns_defaults_on_corrupt_file(tmp_path):
    path = tmp_path / "settings.json"
    path.write_text("not valid json")

    config = load_key_bindings(path)

    assert config == KeyBindingConfig()
