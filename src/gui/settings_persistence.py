"""Save/load KeyBindingConfig to/from a JSON file on disk.

Settings are user preferences edited via the GUI's SettingsPanel, so this
lives alongside the GUI rather than in src.models (which stays I/O-free) or
src.control (which only executes bindings, it doesn't store them).
"""

from __future__ import annotations

import json
from pathlib import Path

from src.models import Gesture, GestureBinding, InputAction, KeyBindingConfig

DEFAULT_SETTINGS_PATH = Path.home() / ".projector_whiteboard" / "settings.json"


def save_key_bindings(config: KeyBindingConfig, path: Path = DEFAULT_SETTINGS_PATH) -> None:
    """Write the given KeyBindingConfig to disk as JSON."""
    payload = {
        "bindings": [
            {"gesture": binding.gesture.value, "action": binding.action.value, "key": binding.key}
            for binding in config.bindings
        ]
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2))


def load_key_bindings(path: Path = DEFAULT_SETTINGS_PATH) -> KeyBindingConfig:
    """Read a KeyBindingConfig from disk, falling back to defaults if missing/invalid."""
    if not path.exists():
        return KeyBindingConfig()

    try:
        payload = json.loads(path.read_text())
        bindings = tuple(
            GestureBinding(
                gesture=Gesture(entry["gesture"]),
                action=InputAction(entry["action"]),
                key=entry.get("key"),
            )
            for entry in payload["bindings"]
        )
        return KeyBindingConfig(bindings=bindings)
    except (json.JSONDecodeError, KeyError, ValueError, TypeError):
        return KeyBindingConfig()
