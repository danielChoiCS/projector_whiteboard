"""A single gesture-to-input-action assignment."""

from __future__ import annotations

from dataclasses import dataclass

from src.models.gesture import Gesture
from src.models.input_action import InputAction


@dataclass(frozen=True)
class GestureBinding:
    """One gesture's assigned input action.

    Attributes:
        gesture: The recognized gesture this binding applies to.
        action: The input action to perform while the gesture is active.
        key: Keyboard key name (e.g. "space", "a"), used only when
            ``action`` is ``InputAction.KEY_PRESS``.
    """

    gesture: Gesture
    action: InputAction
    key: str | None = None
