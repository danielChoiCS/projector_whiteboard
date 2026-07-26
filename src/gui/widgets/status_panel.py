"""Overall application status display."""

from __future__ import annotations

from PySide6.QtWidgets import QFormLayout, QGroupBox, QLabel, QWidget

from src.models import ApplicationState


class StatusPanel(QGroupBox):
    """Shows current system state and any error/status messages."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Application Status", parent)

        self._state_label = QLabel("-")
        self._message_label = QLabel("-")
        self._message_label.setWordWrap(True)

        layout = QFormLayout(self)
        layout.addRow("State:", self._state_label)
        layout.addRow("Message:", self._message_label)

    def update_application_state(self, state: ApplicationState) -> None:
        """Update the panel to reflect the given application state."""
        self._state_label.setText(state.system_state.value)
        self._message_label.setText(state.error or state.message)
