"""Camera capture worker: opens a cv2.VideoCapture and emits frames on a timer.

Meant to be moved to a worker QThread before start() is called (see
CameraPipeline) -- opening/reading a VideoCapture blocks, and that must stay
off the GUI thread per the project's threading rules.
"""

from __future__ import annotations

import contextlib
import io
import os
import sys
from typing import Callable

import cv2
import numpy as np
from PySide6.QtCore import QObject, QTimer, Signal

_DEFAULT_FPS = 30


@contextlib.contextmanager
def _suppress_native_stderr():
    """Best-effort suppression of native (non-Python) stderr writes.

    Some OpenCV camera backends (notably macOS's AVFoundation) print directly
    to the OS-level stderr file descriptor when probing a nonexistent device
    index -- e.g. "OpenCV: out device of bound (0-2): 3" -- bypassing
    sys.stderr entirely, so only an actual file-descriptor swap silences it.
    Falls back to doing nothing if stderr isn't fd-backed (e.g. under some
    test-output-capture configurations).
    """
    try:
        stderr_fd = sys.stderr.fileno()
        saved_fd = os.dup(stderr_fd)
    except (OSError, io.UnsupportedOperation, ValueError):
        yield
        return

    devnull_fd = os.open(os.devnull, os.O_WRONLY)
    try:
        os.dup2(devnull_fd, stderr_fd)
        yield
    finally:
        os.close(devnull_fd)
        os.dup2(saved_fd, stderr_fd)
        os.close(saved_fd)


def camera_is_available(device_index: int = 0, capture_factory: Callable = cv2.VideoCapture) -> bool:
    """Check whether a camera device can be opened and actually delivers a frame.

    isOpened() alone isn't a reliable signal: some backends (notably macOS's
    AVFoundation) report a nonexistent index as "opened" and only fail once a
    frame is actually requested, which would otherwise list phantom cameras
    that don't exist.
    """
    with _suppress_native_stderr():
        capture = capture_factory(device_index)
        try:
            if not capture.isOpened():
                return False
            ok, frame = capture.read()
            return bool(ok) and frame is not None
        finally:
            capture.release()


def list_camera_devices(max_index: int = 5, capture_factory: Callable = cv2.VideoCapture) -> list[int]:
    """Probe device indices [0, max_index) and return the ones that open."""
    return [i for i in range(max_index) if camera_is_available(i, capture_factory)]


class CameraWorker(QObject):
    """Captures frames from a camera device and emits them as they arrive."""

    frame_ready = Signal(np.ndarray)
    camera_unavailable = Signal(str)
    _stop_requested = Signal()

    def __init__(
        self,
        device_index: int = 0,
        fps: int = _DEFAULT_FPS,
        capture_factory: Callable = cv2.VideoCapture,
    ) -> None:
        super().__init__()
        self._device_index = device_index
        self._interval_ms = round(1000 / fps)
        self._capture_factory = capture_factory
        self._capture = None
        self._timer: QTimer | None = None
        # stop() touches a QTimer, which may only be stopped from the thread
        # that owns it. request_stop() is the thread-safe entry point: since
        # sender and receiver here are the same object, Qt auto-queues this
        # onto whichever thread this worker actually lives on.
        self._stop_requested.connect(self.stop)

    def request_stop(self) -> None:
        """Thread-safe: stop capturing, regardless of which thread calls this."""
        self._stop_requested.emit()

    def start(self) -> None:
        """Open the camera and begin emitting frames on a timer."""
        with _suppress_native_stderr():
            self._capture = self._capture_factory(self._device_index)
            is_opened = self._capture.isOpened()
        if not is_opened:
            self.camera_unavailable.emit(f"Could not open camera {self._device_index}")
            self._capture = None
            return

        self._timer = QTimer(self)
        self._timer.setInterval(self._interval_ms)
        self._timer.timeout.connect(self._grab_frame)
        self._timer.start()

    def stop(self) -> None:
        """Stop capturing and release the camera device.

        Must be called on this worker's own thread -- use request_stop() from
        anywhere else (e.g. the GUI thread).
        """
        if self._timer is not None:
            self._timer.stop()
            self._timer = None
        if self._capture is not None:
            self._capture.release()
            self._capture = None

    def _grab_frame(self) -> None:
        ok, frame = self._capture.read()
        if not ok:
            self.camera_unavailable.emit("Lost connection to camera")
            self.stop()
            return
        self.frame_ready.emit(frame)
