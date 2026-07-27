"""Hand landmark type and index constants, matching MediaPipe Hands' topology."""

from __future__ import annotations

Landmark = tuple[float, float, float]
HandLandmarks = list[Landmark]

WRIST = 0

THUMB_TIP = 4

INDEX_PIP = 6
INDEX_TIP = 8

MIDDLE_MCP = 9
MIDDLE_PIP = 10
MIDDLE_TIP = 12

RING_PIP = 14
RING_TIP = 16

PINKY_PIP = 18
PINKY_TIP = 20
