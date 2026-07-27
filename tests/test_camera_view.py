import numpy as np
from PySide6.QtGui import QImage

from src.gui.widgets.camera_view import CameraViewWidget
from src.models import CalibrationMode, CalibrationState, Gesture, HandState


def _render(widget: CameraViewWidget) -> QImage:
    image = QImage(widget.size(), QImage.Format.Format_ARGB32)
    widget.render(image)
    return image


def test_hand_overlay_renders_on_top_of_the_live_frame(qapp):
    # Regression test: the overlay used to be painted on the parent widget
    # while the live frame was shown via a child QLabel on top of it, which
    # silently hid the overlay entirely -- this checks actual rendered pixels,
    # not just that update_hand_overlay() doesn't crash.
    widget = CameraViewWidget()
    widget.resize(320, 240)

    frame = np.zeros((240, 320, 3), dtype=np.uint8)
    frame[:, :, 2] = 255  # solid red, BGR
    widget.show_frame(frame)
    widget.update_hand_overlay(
        HandState(detected=True, x=0.5, y=0.5, gesture=Gesture.MOVE, confidence=0.9, timestamp=0.0)
    )

    image = _render(widget)
    center = image.pixelColor(160, 120)
    edge = image.pixelColor(5, 5)

    assert edge.red() > 150 and edge.blue() < 100  # the frame shows at the edge
    assert center.blue() > 150 and center.green() > 150 and center.red() < 100  # cyan hand dot


def test_calibration_corners_render_on_top_of_the_live_frame(qapp):
    widget = CameraViewWidget()
    widget.resize(320, 240)

    frame = np.zeros((240, 320, 3), dtype=np.uint8)
    frame[:, :, 2] = 255
    widget.show_frame(frame)
    widget.update_calibration_overlay(
        CalibrationState(
            calibrated=True,
            in_progress=False,
            progress=1.0,
            transform_available=True,
            status_message="ok",
            mode=CalibrationMode.CONTOUR_DETECTION,
            corners=((0.1, 0.1), (0.9, 0.1), (0.9, 0.9), (0.1, 0.9)),
        )
    )

    image = _render(widget)
    corner_pixel = image.pixelColor(int(0.1 * 320), int(0.1 * 240))

    assert corner_pixel.green() > 150 and corner_pixel.red() < 100


def test_hand_overlay_cleared_when_not_detected(qapp):
    widget = CameraViewWidget()
    widget.resize(320, 240)
    widget.update_hand_overlay(
        HandState(detected=True, x=0.5, y=0.5, gesture=Gesture.MOVE, confidence=0.9, timestamp=0.0)
    )
    assert widget._hand_overlay is not None

    widget.update_hand_overlay(
        HandState(detected=False, x=0.0, y=0.0, gesture=Gesture.NONE, confidence=0.0, timestamp=0.0)
    )

    assert widget._hand_overlay is None


def test_show_unavailable_clears_the_frame(qapp):
    widget = CameraViewWidget()
    frame = np.zeros((4, 4, 3), dtype=np.uint8)
    widget.show_frame(frame)
    assert widget._pixmap is not None

    widget.show_unavailable("no camera")

    assert widget._pixmap is None
