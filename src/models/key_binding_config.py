"""The full set of gesture-to-input-action bindings, edited via GUI settings."""

from __future__ import annotations

from dataclasses import dataclass, field

from src.models.gesture import Gesture
from src.models.gesture_binding import GestureBinding
from src.models.input_action import InputAction


def _default_bindings() -> tuple[GestureBinding, ...]:
    # Only MOVE/CLICK are supported for now -- see gesture_classifier.py.
    # Gesture.DRAG/SCROLL still exist as values but have no default binding.
    #
    # CLICK defaults to MOUSE_DRAG (hold-to-drag), not a single MOUSE_LEFT_CLICK:
    # InputController.dispatch() keeps moving the cursor to the pinch position
    # on every subsequent call while MOUSE_DRAG is held, whereas a bare click
    # is edge-triggered and freezes the cursor at the activation position
    # until the gesture changes. A brief pinch-and-release still behaves like
    # an ordinary click (mouseDown immediately followed by mouseUp).
    return (
        GestureBinding(Gesture.MOVE, InputAction.MOUSE_MOVE),
        GestureBinding(Gesture.CLICK, InputAction.MOUSE_DRAG),
    )


@dataclass(frozen=True)
class KeyBindingConfig:
    """User-configurable mapping from each gesture to an input action.

    Attributes:
        bindings: One GestureBinding per configurable gesture.
    """

    bindings: tuple[GestureBinding, ...] = field(default_factory=_default_bindings)

    def action_for(self, gesture: Gesture) -> GestureBinding | None:
        """Return the binding assigned to the given gesture, if any."""
        return next((binding for binding in self.bindings if binding.gesture == gesture), None)
