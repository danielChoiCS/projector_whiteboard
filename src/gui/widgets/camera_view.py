"""Camera preview widget.

Shows the live camera feed when one is available (fed frame-by-frame via
show_frame()), or a placeholder when it isn't. The frame/placeholder and all
overlays (calibration corners, tracked hand, manual markers) are drawn
together in one paintEvent, not via a child QLabel showing the frame
underneath a separately painted overlay -- child widgets always paint on top
of their parent, which would let the live frame visually cover the overlay.
"""

from __future__ import annotations

import numpy as np
from PySide6.QtCore import QPointF, QRectF, Qt, Signal
from PySide6.QtGui import (
    QColor,
    QImage,
    QMouseEvent,
    QPainter,
    QPaintEvent,
    QPixmap,
    QPolygonF,
)
from PySide6.QtWidgets import QWidget

from src.models import CalibrationState, HandState

_MARKER_RADIUS = 6
_CORNER_RADIUS = 5
_HAND_RADIUS = 8
_PLACEHOLDER_BACKGROUND = QColor("#202020")
_PLACEHOLDER_BORDER = QColor("#404040")
_PLACEHOLDER_TEXT_COLOR = QColor("#a0a0a0")


class CameraViewWidget(QWidget):
    """Displays the camera feed, or a placeholder when unavailable.

    Also accepts left-clicks for manual corner placement: clicking emits
    ``corner_clicked`` with the click position normalized to [0, 1] over the
    widget's current size, and renders a marker dot at that position.

    update_calibration_overlay()/update_hand_overlay() draw the automatically
    detected calibration corners and the currently tracked hand position, both
    normalized [0, 1] over the widget's current size, same as manual markers.
    """

    corner_clicked = Signal(float, float)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._markers: list[tuple[float, float]] = []
        self._calibration_corners: tuple[tuple[float, float], ...] | None = None
        self._hand_overlay: HandState | None = None
        self._pixmap: QPixmap | None = None
        self._placeholder_text = "Camera unavailable"

        self.setMinimumSize(320, 240)

    @property
    def marker_count(self) -> int:
        """Number of corner markers currently placed."""
        return len(self._markers)

    def add_marker(self, x: float, y: float) -> None:
        """Add a corner marker at the given normalized [0, 1] position."""
        self._markers.append((x, y))
        self.update()

    def clear_markers(self) -> None:
        """Remove all placed corner markers."""
        self._markers.clear()
        self.update()

    def update_calibration_overlay(self, state: CalibrationState) -> None:
        """Show the automatically detected calibration corners, if any."""
        self._calibration_corners = state.corners
        self.update()

    def update_hand_overlay(self, state: HandState) -> None:
        """Show the currently tracked hand position and gesture, if detected."""
        self._hand_overlay = state if state.detected else None
        self.update()

    def show_frame(self, frame: np.ndarray) -> None:
        """Display one live BGR camera frame, replacing the placeholder."""
        rgb = np.ascontiguousarray(frame[:, :, ::-1])
        height, width, _ = rgb.shape
        image = QImage(rgb.data, width, height, rgb.strides[0], QImage.Format.Format_RGB888)
        self._pixmap = QPixmap.fromImage(image)
        self.update()

    def show_unavailable(self, message: str = "Camera unavailable") -> None:
        """Revert to the placeholder text (e.g. when the camera disconnects)."""
        self._pixmap = None
        self._placeholder_text = message
        self.update()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Emit corner_clicked with the click position normalized to widget size."""
        if event.button() == Qt.MouseButton.LeftButton:
            width = max(self.width(), 1)
            height = max(self.height(), 1)
            position = event.position()
            self.corner_clicked.emit(position.x() / width, position.y() / height)
        super().mousePressEvent(event)

    def paintEvent(self, event: QPaintEvent) -> None:
        """Draw the frame/placeholder, then calibration/hand/marker overlays on top."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        self._paint_frame_or_placeholder(painter)

        if self._calibration_corners:
            self._paint_calibration_corners(painter)

        painter.setPen(Qt.GlobalColor.black)
        painter.setBrush(Qt.GlobalColor.yellow)
        for x, y in self._markers:
            painter.drawEllipse(self._to_widget_point(x, y), _MARKER_RADIUS, _MARKER_RADIUS)

        if self._hand_overlay is not None:
            self._paint_hand_overlay(painter)

    def _paint_frame_or_placeholder(self, painter: QPainter) -> None:
        rect = QRectF(self.rect())
        if self._pixmap is not None:
            scaled = self._pixmap.scaled(
                self.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
            )
            painter.fillRect(rect, Qt.GlobalColor.black)
            origin = QPointF((self.width() - scaled.width()) / 2, (self.height() - scaled.height()) / 2)
            painter.drawPixmap(origin, scaled)
        else:
            painter.fillRect(rect, _PLACEHOLDER_BACKGROUND)
            painter.setPen(_PLACEHOLDER_TEXT_COLOR)
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, self._placeholder_text)

        painter.setPen(_PLACEHOLDER_BORDER)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRect(rect.adjusted(0, 0, -1, -1))

    def _paint_calibration_corners(self, painter: QPainter) -> None:
        points = [self._to_widget_point(x, y) for x, y in self._calibration_corners]
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(Qt.GlobalColor.green)
        painter.drawPolygon(QPolygonF(points))
        painter.setBrush(Qt.GlobalColor.green)
        for point in points:
            painter.drawEllipse(point, _CORNER_RADIUS, _CORNER_RADIUS)

    def _paint_hand_overlay(self, painter: QPainter) -> None:
        center = self._to_widget_point(self._hand_overlay.x, self._hand_overlay.y)
        painter.setBrush(Qt.GlobalColor.cyan)
        painter.setPen(Qt.GlobalColor.black)
        painter.drawEllipse(center, _HAND_RADIUS, _HAND_RADIUS)
        painter.drawText(center + QPointF(_HAND_RADIUS + 4, 0), self._hand_overlay.gesture.value)

    def _to_widget_point(self, x: float, y: float) -> QPointF:
        return QPointF(x * self.width(), y * self.height())
