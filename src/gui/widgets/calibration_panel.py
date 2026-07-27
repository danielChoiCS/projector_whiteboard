"""Calibration controls and status display."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QGroupBox,
    QLabel,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.models import CalibrationMode, CalibrationState

_MODE_LABELS = {
    CalibrationMode.CONTOUR_DETECTION: "Automatic: contrasted board edges",
    CalibrationMode.RED_STICKER: "Automatic: red corner stickers",
    CalibrationMode.MANUAL_CLICK: "Manual: click 4 corners",
}


class CalibrationPanel(QGroupBox):
    """Shows calibration progress/status and requests new calibrations."""

    start_calibration_requested = Signal()
    mode_selected = Signal(CalibrationMode)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Calibration", parent)

        self._mode_combo = QComboBox()
        for mode in (
            CalibrationMode.CONTOUR_DETECTION,
            CalibrationMode.RED_STICKER,
            CalibrationMode.MANUAL_CLICK,
        ):
            self._mode_combo.addItem(_MODE_LABELS[mode], userData=mode)

        self._start_button = QPushButton("Start Calibration")
        self._progress_bar = QProgressBar()
        self._progress_bar.setRange(0, 100)
        self._status_label = QLabel("Not calibrated")

        layout = QVBoxLayout(self)
        layout.addWidget(self._mode_combo)
        layout.addWidget(self._start_button)
        layout.addWidget(self._progress_bar)
        layout.addWidget(self._status_label)

        self._start_button.clicked.connect(self.start_calibration_requested)
        self._mode_combo.currentIndexChanged.connect(self._on_mode_index_changed)

    def _on_mode_index_changed(self, index: int) -> None:
        # Qt's QVariant round-trip flattens CalibrationMode (a str subclass) to a
        # plain str; re-wrap it so mode_selected always carries a real enum member.
        self.mode_selected.emit(CalibrationMode(self._mode_combo.itemData(index)))

    def update_calibration(self, state: CalibrationState) -> None:
        """Update the panel to reflect the given calibration state."""
        self._progress_bar.setValue(round(state.progress * 100))
        self._status_label.setText(state.status_message)
        self._start_button.setEnabled(not state.in_progress)
