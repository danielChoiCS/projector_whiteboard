"""Corner detection via red sticker markers placed on the whiteboard corners."""

from __future__ import annotations

import cv2
import numpy as np

from src.calibration.geometry import Point

_MIN_STICKER_AREA = 40.0

# Red wraps around hue 0 in OpenCV's 0-179 HSV range, so two ranges are needed.
_LOWER_RED_1 = np.array([0, 120, 70])
_UPPER_RED_1 = np.array([10, 255, 255])
_LOWER_RED_2 = np.array([170, 120, 70])
_UPPER_RED_2 = np.array([180, 255, 255])


def detect_red_sticker_corners(frame: np.ndarray) -> list[Point] | None:
    """Locate up to four red sticker markers and return their centroids.

    Args:
        frame: BGR image, as produced by an OpenCV camera capture.

    Returns:
        The centroids of the four largest red blobs found, or None if fewer
        than four are detected.
    """
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, _LOWER_RED_1, _UPPER_RED_1) | cv2.inRange(
        hsv, _LOWER_RED_2, _UPPER_RED_2
    )
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    candidates = [c for c in contours if cv2.contourArea(c) >= _MIN_STICKER_AREA]
    if len(candidates) < 4:
        return None

    candidates.sort(key=cv2.contourArea, reverse=True)
    centroids: list[Point] = []
    for contour in candidates[:4]:
        moments = cv2.moments(contour)
        cx = moments["m10"] / moments["m00"]
        cy = moments["m01"] / moments["m00"]
        centroids.append((cx, cy))
    return centroids
