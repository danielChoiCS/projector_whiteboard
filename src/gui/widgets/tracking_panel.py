"""Hand tracking status display."""

from __future__ import annotations

from PySide6.QtWidgets import QFormLayout, QGroupBox, QLabel, QWidget

from src.models import HandState


class TrackingPanel(QGroupBox):
    """Shows current hand detection, gesture, and confidence."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Tracking", parent)

        self._detected_label = QLabel("No")
        self._gesture_label = QLabel("-")
        self._confidence_label = QLabel("-")

        layout = QFormLayout(self)
        layout.addRow("Hand detected:", self._detected_label)
        layout.addRow("Gesture:", self._gesture_label)
        layout.addRow("Confidence:", self._confidence_label)

    def update_hand_state(self, state: HandState) -> None:
        """Update the panel to reflect the given hand tracking state."""
        self._detected_label.setText("Yes" if state.detected else "No")
        self._gesture_label.setText(state.gesture.value if state.detected else "-")
        self._confidence_label.setText(f"{state.confidence:.2f}" if state.detected else "-")
