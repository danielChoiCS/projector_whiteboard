"""Mock providers that let the GUI run before vision/calibration exist.

MockHandProvider stands in only for the *camera* — it drives the real
classify_gesture/hand_position functions (src.vision) against synthetic hand
landmark poses, so the gesture recognition it exercises is genuine, not a
simulation of it. MockCalibrationProvider does the same for calibration,
driving the real CalibrationEngine (src.calibration) against synthetically
generated frames. Swapping in a live camera + MediaPipe/OpenCV later only
changes the input source, not the algorithms or the GUI.
"""

from __future__ import annotations

import time
from itertools import cycle

import cv2
import numpy as np
from PySide6.QtCore import QTimer

from src.calibration.engine import CalibrationEngine
from src.gui.providers.base import CalibrationProvider, HandProvider
from src.models import CalibrationMode, CalibrationState, Gesture, HandState
from src.vision.gesture_classifier import classify_gesture, hand_position
from src.vision.landmarks import (
    INDEX_PIP,
    INDEX_TIP,
    MIDDLE_MCP,
    MIDDLE_PIP,
    MIDDLE_TIP,
    PINKY_PIP,
    PINKY_TIP,
    RING_PIP,
    RING_TIP,
    THUMB_TIP,
    WRIST,
    HandLandmarks,
)

_MOCK_STEP_INTERVAL_MS = 1500
_MOCK_CONFIDENCE = 0.9


def _pose_landmarks(
    *, index: bool = False, middle: bool = False, ring: bool = False, pinky: bool = False, pinch: bool = False
) -> HandLandmarks:
    """Build a synthetic 21-point hand pose with the given fingers extended."""
    landmarks: HandLandmarks = [(0.5, 0.5, 0.0)] * 21
    landmarks[WRIST] = (0.5, 0.9, 0.0)
    landmarks[MIDDLE_MCP] = (0.5, 0.6, 0.0)

    def finger(pip_idx: int, tip_idx: int, x: float, extended: bool) -> None:
        landmarks[pip_idx] = (x, 0.55, 0.0)
        landmarks[tip_idx] = (x, 0.35 if extended else 0.65, 0.0)

    finger(INDEX_PIP, INDEX_TIP, 0.45, index)
    finger(MIDDLE_PIP, MIDDLE_TIP, 0.50, middle)
    finger(RING_PIP, RING_TIP, 0.55, ring)
    finger(PINKY_PIP, PINKY_TIP, 0.60, pinky)
    landmarks[THUMB_TIP] = landmarks[INDEX_TIP] if pinch else (0.3, 0.7, 0.0)
    return landmarks


# Only MOVE/CLICK are supported for now -- see gesture_classifier.py.
_HAND_POSES: list[HandLandmarks | None] = [
    None,  # no hand in frame
    _pose_landmarks(index=True, middle=True, ring=True, pinky=True),  # open hand -> MOVE
    _pose_landmarks(index=True, middle=True, ring=True, pinky=True, pinch=True),  # pinch -> CLICK
]


class MockHandProvider(HandProvider):
    """Runs the real gesture classifier against synthetic hand poses."""

    def __init__(self) -> None:
        super().__init__()
        self._poses = cycle(_HAND_POSES)
        self._timer = QTimer(self)
        self._timer.setInterval(_MOCK_STEP_INTERVAL_MS)
        self._timer.timeout.connect(self._emit_next)

    def start(self) -> None:
        """Begin cycling through sample hand poses."""
        self._emit_next()
        self._timer.start()

    def stop(self) -> None:
        """Stop cycling through sample hand poses."""
        self._timer.stop()

    def _emit_next(self) -> None:
        landmarks = next(self._poses)
        if landmarks is None:
            state = HandState(
                detected=False, x=0.0, y=0.0, gesture=Gesture.NONE, confidence=0.0, timestamp=time.time()
            )
        else:
            x, y = hand_position(landmarks)
            state = HandState(
                detected=True,
                x=x,
                y=y,
                gesture=classify_gesture(landmarks),
                confidence=_MOCK_CONFIDENCE,
                timestamp=time.time(),
            )
        self.hand_state_changed.emit(state)


_DEMO_FRAME_SIZE = (480, 360)  # (width, height)
_DEMO_FRAME_MARGIN = 40
_DEMO_TICK_INTERVAL_MS = 300


def _generate_demo_frame(mode: CalibrationMode, size: tuple[int, int]) -> np.ndarray:
    """Render a synthetic frame standing in for a camera capture of the board.

    Draws whatever the selected automatic strategy is meant to detect: a
    bright quadrilateral for contour detection, red corner markers for
    sticker detection.
    """
    width, height = size
    frame = np.zeros((height, width, 3), dtype=np.uint8)
    corners = [
        (_DEMO_FRAME_MARGIN, _DEMO_FRAME_MARGIN),
        (width - _DEMO_FRAME_MARGIN, _DEMO_FRAME_MARGIN),
        (width - _DEMO_FRAME_MARGIN, height - _DEMO_FRAME_MARGIN),
        (_DEMO_FRAME_MARGIN, height - _DEMO_FRAME_MARGIN),
    ]

    if mode == CalibrationMode.RED_STICKER:
        for x, y in corners:
            cv2.circle(frame, (x, y), 8, (0, 0, 255), -1)
    elif mode == CalibrationMode.CONTOUR_DETECTION:
        cv2.fillConvexPoly(frame, np.array(corners, dtype=np.int32), (230, 230, 230))

    return frame


class MockCalibrationProvider(CalibrationProvider):
    """Runs the real CalibrationEngine against synthetic demo frames."""

    def __init__(self) -> None:
        super().__init__()
        self._engine = CalibrationEngine()
        self._timer = QTimer(self)
        self._timer.setInterval(_DEMO_TICK_INTERVAL_MS)
        self._timer.timeout.connect(self._tick)

    def start_calibration(self) -> None:
        """(Re)start calibration using the engine's currently selected mode."""
        self._engine.reset()
        self._emit_state()
        if self._engine.mode == CalibrationMode.MANUAL_CLICK:
            self._timer.stop()
        else:
            self._timer.start()

    def set_mode(self, mode: CalibrationMode) -> None:
        """Switch strategy and discard any in-progress calibration attempt."""
        self._timer.stop()
        self._engine.set_mode(mode)
        self._emit_state()

    def add_manual_point(self, x: float, y: float) -> None:
        """Forward a manually clicked corner to the engine."""
        self._emit_state(self._engine.add_manual_point(x, y))

    def _tick(self) -> None:
        frame = _generate_demo_frame(self._engine.mode, _DEMO_FRAME_SIZE)
        state = self._emit_state(self._engine.process_frame(frame))
        if state.calibrated:
            self._timer.stop()

    def _emit_state(self, state: CalibrationState | None = None) -> CalibrationState:
        state = state or self._engine.state()
        self.calibration_state_changed.emit(state)
        return state
