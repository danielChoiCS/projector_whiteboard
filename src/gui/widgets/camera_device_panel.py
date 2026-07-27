"""Camera device selection dropdown."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QComboBox, QGroupBox, QVBoxLayout, QWidget

_SYNTHETIC_LABEL = "No camera (synthetic data)"


class CameraDevicePanel(QGroupBox):
    """Lets the user pick which camera device feeds the app, or none at all."""

    device_selected = Signal(object)  # int device index, or None for synthetic data

    def __init__(
        self,
        available_devices: tuple[int, ...] = (),
        current_device: int | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__("Camera Device", parent)

        self._devices: list[int | None] = [None, *available_devices]
        self._combo = QComboBox()
        self._combo.addItem(_SYNTHETIC_LABEL)
        for device in available_devices:
            self._combo.addItem(f"Camera {device}")

        if current_device in self._devices:
            self._combo.setCurrentIndex(self._devices.index(current_device))

        layout = QVBoxLayout(self)
        layout.addWidget(self._combo)

        self._combo.currentIndexChanged.connect(self._on_index_changed)

    def _on_index_changed(self, index: int) -> None:
        self.device_selected.emit(self._devices[index])
