"""Hand tracking data model, produced by the vision subsystem."""

from dataclasses import dataclass

from src.models.gesture import Gesture


@dataclass(frozen=True)
class HandState:
    """Snapshot of hand tracking output at a single point in time.

    Attributes:
        detected: Whether a hand is currently detected in frame.
        x: Normalized horizontal hand position in [0.0, 1.0]. Meaningless
            when ``detected`` is False.
        y: Normalized vertical hand position in [0.0, 1.0]. Meaningless
            when ``detected`` is False.
        gesture: Currently recognized gesture.
        confidence: Tracking confidence in [0.0, 1.0].
        timestamp: Seconds since epoch when this state was produced.
    """

    detected: bool
    x: float
    y: float
    gesture: Gesture
    confidence: float
    timestamp: float
