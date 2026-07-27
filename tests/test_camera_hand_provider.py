import numpy as np

from src.gui.providers.camera_hand_provider import CameraHandProvider
from src.models import Gesture, HandState


class _FakeTracker:
    def __init__(self):
        self.processed = []
        self.closed = False

    def process(self, frame, timestamp):
        self.processed.append((frame, timestamp))
        return HandState(detected=True, x=0.1, y=0.2, gesture=Gesture.MOVE, confidence=1.0, timestamp=timestamp)

    def close(self):
        self.closed = True


def test_tracker_not_constructed_until_start():
    provider = CameraHandProvider(tracker_factory=_FakeTracker)

    assert provider._tracker is None


def test_start_constructs_tracker_once():
    calls = []

    def factory():
        calls.append(1)
        return _FakeTracker()

    provider = CameraHandProvider(tracker_factory=factory)

    provider.start()
    provider.start()

    assert len(calls) == 1


def test_process_frame_before_start_emits_nothing():
    provider = CameraHandProvider(tracker_factory=_FakeTracker)
    received = []
    provider.hand_state_changed.connect(received.append)

    provider.process_frame(np.zeros((4, 4, 3), dtype=np.uint8))

    assert received == []


def test_process_frame_emits_hand_state_from_tracker():
    provider = CameraHandProvider(tracker_factory=_FakeTracker)
    provider.start()
    received = []
    provider.hand_state_changed.connect(received.append)

    provider.process_frame(np.zeros((4, 4, 3), dtype=np.uint8))

    assert len(received) == 1
    assert received[0].detected
    assert received[0].gesture == Gesture.MOVE


def test_stop_closes_tracker_and_allows_restart():
    provider = CameraHandProvider(tracker_factory=_FakeTracker)
    provider.start()
    tracker = provider._tracker

    provider.stop()

    assert tracker.closed
    assert provider._tracker is None


def test_request_stop_closes_tracker():
    provider = CameraHandProvider(tracker_factory=_FakeTracker)
    provider.start()
    tracker = provider._tracker

    provider.request_stop()

    assert tracker.closed
