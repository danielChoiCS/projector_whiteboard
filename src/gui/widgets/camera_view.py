"""Camera preview widget.

Shows a placeholder until a provider calls show_frame() with a live frame;
falls back to the placeholder again via show_unavailable(). See
src/gui/providers/camera.py for the provider that drives this in practice.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

_PLACEHOLDER_TEXT = "Camera unavailable"
_PLACEHOLDER_STYLE = (
    "background-color: #202020; color: #a0a0a0; border: 1px solid #404040;"
)


class CameraViewWidget(QWidget):
    """Displays the camera feed, or a placeholder when unavailable."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._label = QLabel(_PLACEHOLDER_TEXT)
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._label.setMinimumSize(320, 240)
        self._label.setStyleSheet(_PLACEHOLDER_STYLE)

        layout = QVBoxLayout(self)
        layout.addWidget(self._label)

    def show_frame(self, image: QImage) -> None:
        """Display a live camera frame, scaled to fit the widget."""
        self._label.setStyleSheet("")
        pixmap = QPixmap.fromImage(image).scaled(
            self._label.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self._label.setPixmap(pixmap)

    def show_unavailable(self) -> None:
        """Revert to the placeholder shown when no camera feed is active."""
        self._label.setPixmap(QPixmap())
        self._label.setText(_PLACEHOLDER_TEXT)
        self._label.setStyleSheet(_PLACEHOLDER_STYLE)
