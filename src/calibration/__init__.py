"""Whiteboard calibration: corner detection strategies and the calibration engine.

Pure Python/OpenCV/numpy. No PySide6 dependency and no GUI components.
"""

from src.calibration.contour_detector import detect_contour_corners
from src.calibration.engine import CalibrationEngine
from src.calibration.geometry import compute_homography, order_corners
from src.calibration.red_sticker_detector import detect_red_sticker_corners

__all__ = [
    "CalibrationEngine",
    "compute_homography",
    "detect_contour_corners",
    "detect_red_sticker_corners",
    "order_corners",
]
