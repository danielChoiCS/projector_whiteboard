"""Corner ordering and perspective-transform math shared by all detectors."""

from __future__ import annotations

import cv2
import numpy as np

Point = tuple[float, float]


def order_corners(points: list[Point]) -> list[Point]:
    """Order 4 arbitrary points as (top-left, top-right, bottom-right, bottom-left).

    Uses the standard sum/difference trick: the top-left point has the
    smallest x+y, the bottom-right the largest x+y, the top-right the
    smallest x-y, and the bottom-left the largest x-y.
    """
    pts = np.array(points, dtype=np.float32)
    total = pts.sum(axis=1)
    diff = np.diff(pts, axis=1).flatten()

    top_left = pts[np.argmin(total)]
    bottom_right = pts[np.argmax(total)]
    top_right = pts[np.argmin(diff)]
    bottom_left = pts[np.argmax(diff)]

    return [
        (float(top_left[0]), float(top_left[1])),
        (float(top_right[0]), float(top_right[1])),
        (float(bottom_right[0]), float(bottom_right[1])),
        (float(bottom_left[0]), float(bottom_left[1])),
    ]


_UNIT_SQUARE = np.array([[0, 0], [1, 0], [1, 1], [0, 1]], dtype=np.float32)


def compute_homography(corners: list[Point]) -> np.ndarray:
    """Compute the perspective transform mapping ordered corners to the unit square.

    Args:
        corners: Four normalized [0, 1] points ordered (top-left, top-right,
            bottom-right, bottom-left), as produced by ``order_corners``.

    Returns:
        A 3x3 perspective transform mapping normalized camera-space points to
        normalized [0, 1] screen-space points. The input controller is
        responsible for scaling that output to actual screen pixels, so this
        stays independent of both camera resolution and screen resolution.
    """
    src = np.array(corners, dtype=np.float32)
    return cv2.getPerspectiveTransform(src, _UNIT_SQUARE)
