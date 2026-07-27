import os
import sys

import numpy as np

from src.gui.providers.camera_worker import (
    CameraWorker,
    _suppress_native_stderr,
    camera_is_available,
    list_camera_devices,
)


def test_suppress_native_stderr_restores_stderr_fd_afterward():
    # Actual suppression (fd 2 pointed at devnull during the block) is verified
    # manually -- see camera_worker.py's docstring for how -- since nesting an
    # fd-level swap inside pytest's own fd-level output capture is unreliable
    # to assert on directly. This checks the restore contract holds: the fd
    # number is unchanged and still writable once the block exits.
    stderr_fd_before = sys.stderr.fileno()

    with _suppress_native_stderr():
        pass

    assert sys.stderr.fileno() == stderr_fd_before
    os.write(stderr_fd_before, b"")


class _FakeCapture:
    def __init__(self, opened=True, frames=None):
        self._opened = opened
        self._frames = frames or []
        self._index = 0
        self.released = False

    def isOpened(self):
        return self._opened

    def read(self):
        if self._index < len(self._frames):
            frame = self._frames[self._index]
            self._index += 1
            return True, frame
        return False, None

    def release(self):
        self.released = True


_SAMPLE_FRAME = np.zeros((4, 4, 3), dtype=np.uint8)


def _factory(opened=True, frames=None):
    return lambda device_index: _FakeCapture(opened=opened, frames=frames)


def test_camera_is_available_true_when_capture_opens_and_reads():
    assert camera_is_available(capture_factory=_factory(opened=True, frames=[_SAMPLE_FRAME]))


def test_camera_is_available_false_when_capture_fails_to_open():
    assert not camera_is_available(capture_factory=_factory(opened=False))


def test_camera_is_available_false_when_opened_but_no_frame_readable():
    # Simulates a phantom index some backends report as "opened" even though
    # no real device is there -- it should not count as available.
    assert not camera_is_available(capture_factory=_factory(opened=True, frames=[]))


def test_camera_is_available_releases_the_probe_capture():
    captures = []

    def factory(device_index):
        capture = _FakeCapture(opened=True, frames=[_SAMPLE_FRAME])
        captures.append(capture)
        return capture

    camera_is_available(capture_factory=factory)

    assert captures[0].released


def test_list_camera_devices_returns_only_openable_indices():
    def factory(device_index):
        return _FakeCapture(opened=device_index in (0, 2), frames=[_SAMPLE_FRAME])

    assert list_camera_devices(max_index=4, capture_factory=factory) == [0, 2]


def test_list_camera_devices_empty_when_none_open():
    assert list_camera_devices(max_index=3, capture_factory=_factory(opened=False)) == []


def test_list_camera_devices_excludes_phantom_indices_that_open_but_cant_read():
    def factory(device_index):
        return _FakeCapture(opened=True, frames=[])

    assert list_camera_devices(max_index=3, capture_factory=factory) == []


def test_worker_emits_unavailable_when_capture_fails_to_open():
    worker = CameraWorker(capture_factory=_factory(opened=False))
    messages = []
    worker.camera_unavailable.connect(messages.append)

    worker.start()

    assert messages == ["Could not open camera 0"]


def test_worker_grabs_and_emits_a_frame():
    frame = np.zeros((4, 4, 3), dtype=np.uint8)
    worker = CameraWorker(capture_factory=_factory(opened=True, frames=[frame]))
    received = []
    worker.frame_ready.connect(received.append)

    worker.start()
    worker._grab_frame()

    assert len(received) == 1
    assert np.array_equal(received[0], frame)


def test_worker_emits_unavailable_when_read_fails():
    worker = CameraWorker(capture_factory=_factory(opened=True, frames=[]))
    messages = []
    worker.camera_unavailable.connect(messages.append)

    worker.start()
    worker._grab_frame()

    assert messages == ["Lost connection to camera"]


def test_worker_stop_releases_the_capture():
    capture = _FakeCapture(opened=True)
    worker = CameraWorker(capture_factory=lambda device_index: capture)

    worker.start()
    worker.stop()

    assert capture.released


def test_worker_request_stop_releases_the_capture():
    # In this test worker never moves to another thread, so Qt resolves the
    # self-connected signal to a direct (synchronous) call -- verifying the
    # cross-thread queuing mechanism itself is done via CameraPipeline's
    # design (see camera_pipeline.py's docstring on shutdown()).
    capture = _FakeCapture(opened=True)
    worker = CameraWorker(capture_factory=lambda device_index: capture)

    worker.start()
    worker.request_stop()

    assert capture.released
