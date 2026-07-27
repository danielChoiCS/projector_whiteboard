"""Real HandProvider backed by an on-device camera and MediaPipe tracking.

Frame capture and inference run on a worker QThread (via _CameraWorker) so
the Qt event loop never blocks on camera I/O or model inference -- this is
safe because src.vision.hand_tracker.HandTracker.process_frame does no
OpenCV HighGUI window calls (no cv2.imshow/waitKey), unlike calibration's
manual click flow (see manual_calibration.py, which cannot use a worker
thread for that reason).
"""

from __future__ import annotations

import time

import cv2
from PySide6.QtCore import QObject, QThread, Signal
from PySide6.QtGui import QImage

from src.gui.providers.base import HandProvider
from src.models import Gesture, HandState
from src.vision.hand_tracker import HandTracker


class _CameraWorker(QObject):
    """Owns the capture device and the tracker; runs on its own QThread."""

    hand_state_ready = Signal(HandState)
    frame_ready = Signal(QImage)

    def __init__(self, camera_index: int) -> None:
        super().__init__()
        self._camera_index = camera_index
        self._running = False

    def run(self) -> None:
        """Capture/track loop. Runs until stop() flips self._running off."""
        cap = cv2.VideoCapture(self._camera_index)
        tracker = HandTracker()
        self._running = True
        try:
            while self._running:
                ret, frame = cap.read()
                if not ret:
                    self.hand_state_ready.emit(self._no_camera_state())
                    continue

                self._emit_frame(frame)

                h, w = frame.shape[:2]
                raw_state, _ = tracker.process_frame(frame)
                self.hand_state_ready.emit(self._to_hand_state(raw_state, w, h))
        finally:
            tracker.close()
            cap.release()

    def stop(self) -> None:
        """Signal the loop in run() to exit on its next iteration."""
        self._running = False

    def _emit_frame(self, frame) -> None:
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w = rgb.shape[:2]
        image = QImage(rgb.data, w, h, rgb.strides[0], QImage.Format.Format_RGB888).copy()
        self.frame_ready.emit(image)

    @staticmethod
    def _no_camera_state() -> HandState:
        return HandState(
            detected=False,
            x=0.0,
            y=0.0,
            gesture=Gesture.NONE,
            confidence=0.0,
            timestamp=time.time(),
            camera_connected=False,
        )

    @staticmethod
    def _to_hand_state(raw_state: dict | None, frame_w: int, frame_h: int) -> HandState:
        if raw_state is None:
            return HandState(
                detected=False,
                x=0.0,
                y=0.0,
                gesture=Gesture.NONE,
                confidence=0.0,
                timestamp=time.time(),
                camera_connected=True,
            )
        x, y = raw_state["position"]
        return HandState(
            detected=True,
            x=x / frame_w,
            y=y / frame_h,
            gesture=Gesture(raw_state["gesture"]),
            confidence=raw_state["confidence"],
            timestamp=time.time(),
            camera_connected=True,
        )


class CameraHandProvider(HandProvider):
    """HandProvider backed by a real camera and MediaPipe hand tracking."""

    def __init__(self, camera_index: int = 0) -> None:
        super().__init__()
        self._thread = QThread()
        self._worker = _CameraWorker(camera_index)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.hand_state_ready.connect(self.hand_state_changed)
        self._worker.frame_ready.connect(self.frame_ready)

    def start(self) -> None:
        """Start the camera/tracking worker thread."""
        self._thread.start()

    def stop(self) -> None:
        """Stop the worker loop and shut down its thread."""
        self._worker.stop()
        self._thread.quit()
        self._thread.wait()
