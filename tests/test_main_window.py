from src.gui.main_window import MainWindow
from src.gui.providers.mock import MockCalibrationProvider, MockHandProvider
from src.models import CalibrationMode, Gesture, HandState, KeyBindingConfig


def _hand(gesture=Gesture.MOVE, detected=True, x=0.5, y=0.5):
    return HandState(detected=detected, x=x, y=y, gesture=gesture, confidence=1.0, timestamp=0.0)


def test_initial_state_is_uncalibrated_and_no_hand(qapp):
    window = MainWindow(MockHandProvider(), MockCalibrationProvider())

    assert not window.calibration_state.calibrated
    assert window.key_binding_config == KeyBindingConfig()


def test_calibration_state_property_updates_from_provider(qapp):
    hand_provider = MockHandProvider()
    calibration_provider = MockCalibrationProvider()
    window = MainWindow(hand_provider, calibration_provider)

    calibration_provider.set_mode(CalibrationMode.MANUAL_CLICK)
    calibration_provider.start_calibration()
    for point in [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]:
        calibration_provider.add_manual_point(*point)

    assert window.calibration_state.calibrated


def test_key_binding_config_property_updates_and_persists(qapp, tmp_path):
    from src.gui.settings_persistence import load_key_bindings
    from src.gui.widgets.settings_panel import _ACTION_ORDER
    from src.models import InputAction

    settings_path = tmp_path / "settings.json"
    window = MainWindow(MockHandProvider(), MockCalibrationProvider(), settings_path=settings_path)

    click_combo = window._settings_panel._action_combos[Gesture.CLICK]
    click_combo.setCurrentIndex(_ACTION_ORDER.index(InputAction.SCROLL_UP))

    assert window.key_binding_config.action_for(Gesture.CLICK).action == InputAction.SCROLL_UP
    assert load_key_bindings(settings_path).action_for(Gesture.CLICK).action == InputAction.SCROLL_UP


def test_corner_clicks_only_add_markers_in_manual_mode(qapp):
    window = MainWindow(MockHandProvider(), MockCalibrationProvider())

    # Mode changes must go through the panel's signal, not the provider directly --
    # that's what actually updates MainWindow._current_calibration_mode.
    window._calibration_panel.mode_selected.emit(CalibrationMode.CONTOUR_DETECTION)
    window._camera_view.corner_clicked.emit(0.1, 0.1)
    assert window._camera_view.marker_count == 0

    window._calibration_panel.mode_selected.emit(CalibrationMode.MANUAL_CLICK)
    window._camera_view.corner_clicked.emit(0.1, 0.1)
    assert window._camera_view.marker_count == 1


def test_corner_clicks_stop_adding_markers_past_four(qapp):
    window = MainWindow(MockHandProvider(), MockCalibrationProvider())
    window._calibration_panel.mode_selected.emit(CalibrationMode.MANUAL_CLICK)

    for point in [(0.1, 0.1), (0.2, 0.1), (0.2, 0.2), (0.1, 0.2), (0.5, 0.5)]:
        window._camera_view.corner_clicked.emit(*point)

    assert window._camera_view.marker_count == 4


def test_show_camera_frame_and_unavailable_toggle_camera_connected(qapp):
    import numpy as np

    window = MainWindow(MockHandProvider(), MockCalibrationProvider())

    window.show_camera_frame(np.zeros((4, 4, 3), dtype=np.uint8))
    assert window._camera_connected is True

    window.show_camera_unavailable("no camera")
    assert window._camera_connected is False


def test_hand_state_updates_tracking_overlay(qapp):
    hand_provider = MockHandProvider()
    window = MainWindow(hand_provider, MockCalibrationProvider())

    hand_provider.hand_state_changed.emit(_hand(gesture=Gesture.CLICK))

    assert window._camera_view._hand_overlay is not None
    assert window._camera_view._hand_overlay.gesture == Gesture.CLICK


def test_set_providers_swaps_providers_and_ignores_old_signals(qapp):
    hand1, calib1 = MockHandProvider(), MockCalibrationProvider()
    window = MainWindow(hand1, calib1)

    hand2, calib2 = MockHandProvider(), MockCalibrationProvider()
    window.set_providers(hand2, calib2)

    assert not window.calibration_state.calibrated

    hand1.hand_state_changed.emit(_hand(x=0.9, y=0.9))
    assert window._latest_hand_state.detected is False  # old provider ignored

    hand2.hand_state_changed.emit(_hand(x=0.9, y=0.9))
    assert window._latest_hand_state.detected is True  # new provider picked up


def test_set_providers_resets_camera_overlay_state(qapp):
    hand1, calib1 = MockHandProvider(), MockCalibrationProvider()
    window = MainWindow(hand1, calib1)
    hand1.hand_state_changed.emit(_hand())
    assert window._camera_view._hand_overlay is not None

    window.set_providers(MockHandProvider(), MockCalibrationProvider())

    assert window._camera_view._hand_overlay is None
    assert window._camera_connected is False


def test_camera_device_panel_selection_forwarded_to_window_signal(qapp):
    window = MainWindow(
        MockHandProvider(),
        MockCalibrationProvider(),
        available_camera_devices=(0, 1),
        current_camera_device=0,
    )
    selections = []
    window.camera_device_selected.connect(selections.append)

    window._camera_device_panel._combo.setCurrentIndex(2)  # -> device 1

    assert selections == [1]
