"""Settings panel: assigns each gesture to a mouse/keyboard input action."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QComboBox, QFormLayout, QGroupBox, QLineEdit, QWidget

from src.models import Gesture, GestureBinding, InputAction, KeyBindingConfig

# Only MOVE/CLICK are supported for now -- see gesture_classifier.py.
_CONFIGURABLE_GESTURES = (Gesture.MOVE, Gesture.CLICK)

_ACTION_ORDER = (
    InputAction.NONE,
    InputAction.MOUSE_MOVE,
    InputAction.MOUSE_LEFT_CLICK,
    InputAction.MOUSE_RIGHT_CLICK,
    InputAction.MOUSE_DRAG,
    InputAction.SCROLL_UP,
    InputAction.SCROLL_DOWN,
    InputAction.KEY_PRESS,
)

_ACTION_LABELS = {
    InputAction.NONE: "No action",
    InputAction.MOUSE_MOVE: "Move mouse",
    InputAction.MOUSE_LEFT_CLICK: "Left click",
    InputAction.MOUSE_RIGHT_CLICK: "Right click",
    InputAction.MOUSE_DRAG: "Drag",
    InputAction.SCROLL_UP: "Scroll up",
    InputAction.SCROLL_DOWN: "Scroll down",
    InputAction.KEY_PRESS: "Press key...",
}


class SettingsPanel(QGroupBox):
    """Lets the user assign each gesture to a mouse/keyboard input action.

    Emits the full KeyBindingConfig whenever any row changes; the input
    controller (once implemented) is the consumer, via MainWindow.
    """

    bindings_changed = Signal(KeyBindingConfig)

    def __init__(
        self, initial_config: KeyBindingConfig | None = None, parent: QWidget | None = None
    ) -> None:
        super().__init__("Settings", parent)
        config = initial_config or KeyBindingConfig()

        self._action_combos: dict[Gesture, QComboBox] = {}
        self._key_edits: dict[Gesture, QLineEdit] = {}

        layout = QFormLayout(self)
        for gesture in _CONFIGURABLE_GESTURES:
            binding = config.action_for(gesture)

            action_combo = QComboBox()
            action_combo.addItems([_ACTION_LABELS[action] for action in _ACTION_ORDER])
            if binding is not None:
                action_combo.setCurrentIndex(_ACTION_ORDER.index(binding.action))

            key_edit = QLineEdit(binding.key if binding and binding.key else "")
            key_edit.setPlaceholderText("key name, e.g. space")
            key_edit.setEnabled(binding is not None and binding.action == InputAction.KEY_PRESS)

            action_combo.currentIndexChanged.connect(
                lambda index, edit=key_edit: self._on_action_changed(index, edit)
            )
            key_edit.editingFinished.connect(self._emit_bindings)

            layout.addRow(f"{gesture.value.capitalize()}:", action_combo)
            layout.addRow("", key_edit)

            self._action_combos[gesture] = action_combo
            self._key_edits[gesture] = key_edit

    def _on_action_changed(self, index: int, key_edit: QLineEdit) -> None:
        key_edit.setEnabled(_ACTION_ORDER[index] == InputAction.KEY_PRESS)
        self._emit_bindings()

    def _emit_bindings(self) -> None:
        bindings = tuple(
            GestureBinding(
                gesture=gesture,
                action=_ACTION_ORDER[self._action_combos[gesture].currentIndex()],
                key=self._key_edits[gesture].text() or None,
            )
            for gesture in _CONFIGURABLE_GESTURES
        )
        self.bindings_changed.emit(KeyBindingConfig(bindings=bindings))
