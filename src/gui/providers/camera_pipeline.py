"""Live camera pipeline: wires capture, hand tracking, and calibration onto
one worker QThread, exposing the same hand_provider/calibration_provider
interface the mock providers satisfy.

Camera capture, MediaPipe inference, and calibration frame processing all
share a single worker thread rather than three separate ones -- simpler to
reason about, and fast enough for one hand at a time. Only the resulting
HandState/CalibrationState signals cross back to the GUI thread, which Qt
does automatically for connections to another QObject's bound methods.
"""

from __future__ import annotations

from typing import Callable

from PySide6.QtCore import QThread

from src.gui.providers.camera_calibration_provider import CameraCalibrationProvider
from src.gui.providers.camera_hand_provider import CameraHandProvider
from src.gui.providers.camera_worker import (
    CameraWorker,
    camera_is_available,
    list_camera_devices,
)

__all__ = ["CameraPipeline", "camera_is_available", "list_camera_devices"]


class CameraPipeline:
    """Owns the camera worker thread and its hand/calibration providers."""

    def __init__(self, device_index: int = 0) -> None:
        self.hand_provider = CameraHandProvider()
        self.calibration_provider = CameraCalibrationProvider()
        self._worker = CameraWorker(device_index=device_index)
        self._thread = QThread()

        self._worker.moveToThread(self._thread)
        self.hand_provider.moveToThread(self._thread)
        self.calibration_provider.moveToThread(self._thread)

        self._worker.frame_ready.connect(self.hand_provider.process_frame)
        self._worker.frame_ready.connect(self.calibration_provider.process_frame)
        self._thread.started.connect(self._worker.start)
        self._thread.started.connect(self.hand_provider.start)

    def start(self) -> None:
        """Start the worker thread; camera capture and tracking begin immediately."""
        self._thread.start()

    def connect_frame_preview(self, slot: Callable) -> None:
        """Connect a slot to receive raw camera frames (e.g. for a live preview)."""
        self._worker.frame_ready.connect(slot)

    def connect_camera_unavailable(self, slot: Callable) -> None:
        """Connect a slot to be notified if the camera becomes unavailable."""
        self._worker.camera_unavailable.connect(slot)

    def shutdown(self) -> None:
        """Stop capture, release the hand tracker, and stop the worker thread.

        Safe to call from any thread: request_stop() queues the actual
        stop() work onto the worker thread these objects live on, rather
        than running it here directly (which previously caused
        "QObject::killTimer: Timers cannot be stopped from another thread").
        """
        self._worker.request_stop()
        self.hand_provider.request_stop()
        self._thread.quit()
        self._thread.wait()
