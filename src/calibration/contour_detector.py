"""Fully automatic corner detection via the whiteboard's high-contrast edge."""

from __future__ import annotations

import cv2
import numpy as np

from src.calibration.geometry import Point

_MIN_BOARD_AREA_RATIO = 0.1
_APPROX_EPSILON_RATIO = 0.02


def detect_contour_corners(frame: np.ndarray) -> list[Point] | None:
    """Find the largest high-contrast quadrilateral in the frame.

    Args:
        frame: BGR image, as produced by an OpenCV camera capture.

    Returns:
        The four corners of the largest convex quadrilateral contour big
        enough to plausibly be the whiteboard, or None if none is found.
    """
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blurred, 50, 150)
    edges = cv2.dilate(edges, np.ones((3, 3), np.uint8))

    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    min_area = frame.shape[0] * frame.shape[1] * _MIN_BOARD_AREA_RATIO

    best: list[Point] | None = None
    best_area = 0.0
    for contour in contours:
        area = cv2.contourArea(contour)
        if area < min_area or area <= best_area:
            continue
        perimeter = cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, _APPROX_EPSILON_RATIO * perimeter, True)
        if len(approx) == 4 and cv2.isContourConvex(approx):
            best = [(float(point[0][0]), float(point[0][1])) for point in approx]
            best_area = area

    return best
