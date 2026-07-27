"""Real HandProvider: runs MediaPipe hand tracking on live camera frames."""

from __future__ import annotations

import time
from typing import Callable

import numpy as np

from src.gui.providers.base import HandProvider
from src.vision.hand_tracker import MediaPipeHandTracker


class CameraHandProvider(HandProvider):
    """Feeds camera frames through MediaPipeHandTracker to produce HandState.

    The tracker is constructed lazily in start() rather than __init__, since
    start() is invoked (via CameraPipeline) on the worker thread this
    provider is moved to -- keeping MediaPipe's slow first-import off the
    GUI thread. tracker_factory is injectable so tests can avoid ever
    constructing a real MediaPipeHandTracker.
    """

    def __init__(self, tracker_factory: Callable[[], MediaPipeHandTracker] = MediaPipeHandTracker) -> None:
        super().__init__()
        self._tracker_factory = tracker_factory
        self._tracker: MediaPipeHandTracker | None = None

    def start(self) -> None:
        """Construct the hand tracker if it hasn't been already."""
        if self._tracker is None:
            self._tracker = self._tracker_factory()

    def stop(self) -> None:
        """Release the hand tracker."""
        if self._tracker is not None:
            self._tracker.close()
            self._tracker = None

    def process_frame(self, frame: np.ndarray) -> None:
        """Run hand tracking on one camera frame and emit the resulting HandState."""
        if self._tracker is None:
            return
        state = self._tracker.process(frame, time.time())
        self.hand_state_changed.emit(state)
