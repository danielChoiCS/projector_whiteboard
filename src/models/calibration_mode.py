"""Selectable strategies for locating the whiteboard's corners."""

from enum import Enum


class CalibrationMode(str, Enum):
    """Strategy used to determine the whiteboard's four corners."""

    MANUAL_CLICK = "manual_click"
    RED_STICKER = "red_sticker"
    CONTOUR_DETECTION = "contour_detection"
