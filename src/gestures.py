"""
Gesture interpretation helpers.

Wraps the raw per-frame gesture string from get_hand_state() (in
hand_tracker.py) into edge-triggered events, so callers don't have to
reimplement debounce/cooldown logic everywhere a gesture is used
(calibration, drawing, erasing, and any gesture you add later, like a
two-hand "clear board").
"""


class GestureController:
    def __init__(self, cooldown_frames=15):
        self.cooldown_frames = cooldown_frames
        self._cooldown = 0
        self._active_gesture = None  # gesture currently being "held"

    def update(self, gesture):
        """
        Call once per frame with the current raw gesture
        ("pinch" | "fist" | "point" | None).

        Returns (is_new_trigger, gesture):
          - is_new_trigger is True only on the frame a gesture transitions
            from inactive -> active (e.g. point -> pinch), and only once
            any cooldown from a previous trigger has elapsed. Use this
            for one-shot actions (confirm a calibration corner, clear
            the board, undo, etc).
          - gesture is passed through unchanged every frame, for
            continuous actions that should run for as long as the
            gesture is held (drawing while pinching, erasing while
            a fist is held).
        """
        if self._cooldown > 0:
            self._cooldown -= 1

        is_new_trigger = False
        if gesture != self._active_gesture:
            if gesture is not None and self._cooldown == 0:
                is_new_trigger = True
                self._cooldown = self.cooldown_frames
            self._active_gesture = gesture

        return is_new_trigger, gesture

    def reset(self):
        self._active_gesture = None
        self._cooldown = 0
