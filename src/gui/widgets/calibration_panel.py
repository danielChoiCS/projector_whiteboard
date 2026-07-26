"""Calibration controls and status display."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QGroupBox,
    QLabel,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.models import CalibrationState


class CalibrationPanel(QGroupBox):
    """Shows calibration progress/status and requests new calibrations."""

    start_calibration_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Calibration", parent)

        self._start_button = QPushButton("Start Calibration")
        self._progress_bar = QProgressBar()
        self._progress_bar.setRange(0, 100)
        self._status_label = QLabel("Not calibrated")

        layout = QVBoxLayout(self)
        layout.addWidget(self._start_button)
        layout.addWidget(self._progress_bar)
        layout.addWidget(self._status_label)

        self._start_button.clicked.connect(self.start_calibration_requested)

    def update_calibration(self, state: CalibrationState) -> None:
        """Update the panel to reflect the given calibration state."""
        self._progress_bar.setValue(round(state.progress * 100))
        self._status_label.setText(state.status_message)
        self._start_button.setEnabled(not state.in_progress)
