"""Input controller: converts recognized gestures into OS mouse/keyboard input.

Depends only on src.models and pyautogui -- no PySide6, vision, or
calibration imports.
"""

from src.control.input_controller import InputController

__all__ = ["InputController"]
