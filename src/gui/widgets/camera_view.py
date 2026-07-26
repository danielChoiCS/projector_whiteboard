"""Camera preview widget.

Currently shows a static placeholder. Once the vision team's camera capture
is wired in, this widget's placeholder label will be replaced with a QLabel
driven by incoming QImage frames, without changing its public interface.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class CameraViewWidget(QWidget):
    """Displays the camera feed, or a placeholder when unavailable."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._placeholder = QLabel("Camera unavailable")
        self._placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._placeholder.setMinimumSize(320, 240)
        self._placeholder.setStyleSheet(
            "background-color: #202020; color: #a0a0a0; border: 1px solid #404040;"
        )

        layout = QVBoxLayout(self)
        layout.addWidget(self._placeholder)
