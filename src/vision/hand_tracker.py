"""MediaPipe-backed hand tracker, producing HandState from camera frames.

Uses MediaPipe's Tasks API (mediapipe.tasks.python.vision.HandLandmarker)
rather than the older mp.solutions.hands API: recent mediapipe wheels (0.10.35
confirmed) don't ship mp.solutions at all, only mp.tasks. Unlike the old API,
the Tasks API doesn't bundle its model file in the pip package -- it's
downloaded once, on first use, and cached on disk (see _ensure_model).

MediaPipe is imported lazily inside __init__ rather than at module level: it
pulls in a large runtime, which would otherwise slow down importing
src.vision for anything that only needs the pure gesture classifier (e.g.
tests, the GUI's synthetic-frame demo provider).
"""

from __future__ import annotations

import urllib.request
from pathlib import Path
from typing import Callable

import cv2
import numpy as np

from src.models import Gesture, HandState
from src.vision.gesture_classifier import classify_gesture, hand_position

_DEFAULT_MIN_DETECTION_CONFIDENCE = 0.6

_MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/hand_landmarker/"
    "hand_landmarker/float16/latest/hand_landmarker.task"
)
_DEFAULT_MODEL_PATH = Path.home() / ".projector_whiteboard" / "models" / "hand_landmarker.task"


def _ensure_model(
    model_path: Path = _DEFAULT_MODEL_PATH,
    downloader: Callable[[str, str], object] = urllib.request.urlretrieve,
) -> Path:
    """Download the hand landmark model to model_path if not already cached."""
    if not model_path.exists():
        model_path.parent.mkdir(parents=True, exist_ok=True)
        downloader(_MODEL_URL, str(model_path))
    return model_path


class MediaPipeHandTracker:
    """Runs MediaPipe's HandLandmarker task on camera frames and classifies gestures."""

    def __init__(
        self,
        min_detection_confidence: float = _DEFAULT_MIN_DETECTION_CONFIDENCE,
        model_path: Path = _DEFAULT_MODEL_PATH,
    ) -> None:
        import mediapipe as mp
        from mediapipe.tasks.python.core.base_options import BaseOptions
        from mediapipe.tasks.python.vision import (
            HandLandmarker,
            HandLandmarkerOptions,
            RunningMode,
        )

        self._mp = mp
        options = HandLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=str(_ensure_model(model_path))),
            running_mode=RunningMode.IMAGE,
            num_hands=1,
            min_hand_detection_confidence=min_detection_confidence,
        )
        self._landmarker = HandLandmarker.create_from_options(options)

    def process(self, frame: np.ndarray, timestamp: float) -> HandState:
        """Run hand detection and gesture classification on one BGR frame."""
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = self._mp.Image(image_format=self._mp.ImageFormat.SRGB, data=rgb_frame)
        result = self._landmarker.detect(mp_image)

        if not result.hand_landmarks:
            return HandState(
                detected=False, x=0.0, y=0.0, gesture=Gesture.NONE, confidence=0.0, timestamp=timestamp
            )

        landmarks = [(lm.x, lm.y, lm.z) for lm in result.hand_landmarks[0]]
        x, y = hand_position(landmarks)
        confidence = result.handedness[0][0].score if result.handedness else 1.0
        return HandState(
            detected=True,
            x=x,
            y=y,
            gesture=classify_gesture(landmarks),
            confidence=confidence,
            timestamp=timestamp,
        )

    def close(self) -> None:
        """Release the underlying MediaPipe task."""
        self._landmarker.close()
