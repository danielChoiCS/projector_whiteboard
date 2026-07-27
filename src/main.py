"""Entry point for Project Whiteboard.

Wires a real camera + vision + calibration pipeline into the GUI when a
camera is available, falling back to synthetic mock providers when it isn't
(e.g. no webcam attached) so the app still runs. The user can switch cameras
live via MainWindow's device dropdown; switch_camera() below tears down
whichever pipeline is current and rebuilds MainWindow's providers around the
new choice.

This is also the one place allowed to wire src.control (the gui package
itself never imports it, per the project's dependency rules) to the live
hand-state stream, using MainWindow's calibration_state/key_binding_config
so the input controller always acts on the latest calibration and bindings.
"""

from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from src.control import InputController
from src.gui.main_window import MainWindow
from src.gui.providers import CameraPipeline, list_camera_devices
from src.gui.providers.base import CalibrationProvider, HandProvider
from src.gui.providers.mock import MockCalibrationProvider, MockHandProvider
from src.models import HandState


def _build_providers(
    device: int | None,
) -> tuple[HandProvider, CalibrationProvider, CameraPipeline | None]:
    """Build (hand_provider, calibration_provider, pipeline) for one device choice.

    pipeline is None when device is None (synthetic/mock mode) -- there is
    nothing to start or shut down in that case.
    """
    if device is None:
        return MockHandProvider(), MockCalibrationProvider(), None
    pipeline = CameraPipeline(device_index=device)
    return pipeline.hand_provider, pipeline.calibration_provider, pipeline


def main() -> None:
    """Launch the Project Whiteboard GUI."""
    app = QApplication(sys.argv)

    available_devices = list_camera_devices()
    initial_device = available_devices[0] if available_devices else None
    if initial_device is None:
        print("No camera detected -- running on synthetic mock data instead.", file=sys.stderr)

    hand_provider, calibration_provider, pipeline = _build_providers(initial_device)

    window = MainWindow(
        hand_provider,
        calibration_provider,
        available_camera_devices=tuple(available_devices),
        current_camera_device=initial_device,
    )
    window.resize(720, 480)
    window.show()

    input_controller = InputController()

    def dispatch_to_input_controller(state: HandState) -> None:
        input_controller.dispatch(state, window.calibration_state, window.key_binding_config)

    current = {"pipeline": pipeline, "hand_provider": hand_provider}

    def start_current(pipeline_: CameraPipeline | None, hand_provider_: HandProvider) -> None:
        if pipeline_ is not None:
            pipeline_.connect_frame_preview(window.show_camera_frame)
            pipeline_.connect_camera_unavailable(window.show_camera_unavailable)
            pipeline_.start()
        else:
            window.show_camera_unavailable("Camera unavailable")
            hand_provider_.start()
        hand_provider_.hand_state_changed.connect(dispatch_to_input_controller)

    start_current(pipeline, hand_provider)

    def switch_camera(device: int | None) -> None:
        if current["pipeline"] is not None:
            current["pipeline"].shutdown()  # also requests its hand_provider to stop
        else:
            current["hand_provider"].request_stop()

        new_hand_provider, new_calibration_provider, new_pipeline = _build_providers(device)
        window.set_providers(new_hand_provider, new_calibration_provider)
        start_current(new_pipeline, new_hand_provider)

        current["pipeline"] = new_pipeline
        current["hand_provider"] = new_hand_provider

    def shutdown_current_pipeline() -> None:
        if current["pipeline"] is not None:
            current["pipeline"].shutdown()

    window.camera_device_selected.connect(switch_camera)
    app.aboutToQuit.connect(shutdown_current_pipeline)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
