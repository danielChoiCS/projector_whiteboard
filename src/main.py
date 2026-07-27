<<<<<<< HEAD
"""Entry point for Project Whiteboard.

Wires mock vision/calibration providers into the GUI so it runs before the
real subsystems exist. Swapping in real providers later is a change to this
file only; src/gui and src/models are unaffected.
"""

import sys

from PySide6.QtWidgets import QApplication

from src.gui.main_window import MainWindow
from src.gui.providers.mock import MockCalibrationProvider, MockHandProvider


def main() -> None:
    """Launch the Project Whiteboard GUI."""
    app = QApplication(sys.argv)

    hand_provider = MockHandProvider()
    calibration_provider = MockCalibrationProvider()

    window = MainWindow(hand_provider, calibration_provider)
    window.resize(720, 480)
    window.show()

    sys.exit(app.exec())
=======
"""
Entry point: calibrate the drawing surface by clicking its 4 corners
on the live camera feed, then run the live draw/erase loop
constrained to that surface.

Displays a virtual canvas (plain white background, black ink) rather
than the live camera feed. This avoids a projector/camera feedback
loop: if the raw camera view of the surface were shown/projected back
onto that same surface, the projector's own output would get picked
up by the camera on the next frame, compounding recursively (visible
as mirroring/flicker on the projected surface). The camera is still
used for hand tracking and the calibration homography -- it's just no
longer part of what gets displayed.

During the main loop, press 'r' at any time to re-run calibration
(keyboard only -- see the note by RECALIBRATE_KEY below for why this
is deliberately never gesture-triggered). Existing drawn work is
preserved across a recalibration; only the camera-to-surface mapping
is redone.

--------------------------------------------------------------------------
EXPECTED INTERFACE FROM YOUR HAND-TRACKING MODULE (hand_tracker.py):

    from hand_tracker import get_hand_state

    def get_hand_state(frame) -> dict | None:
        \"\"\"
        Runs your CV model on a single BGR frame and returns either None
        (no hand detected) or a dict:

            {
                "position": (x, y),   # int pixel coords in CAMERA space,
                                       # e.g. the index fingertip landmark
                "gesture":  "point"   # index extended, others curled -> DRAW
                          | "fist"    # closed fist                    -> ERASE
                          | "open"    # relaxed/open hand               -> HOVER
            }

        "position" should be returned regardless of gesture -- i.e. even
        during a fist, still report a representative point (e.g. index
        MCP or palm centroid) so erasing (and the hover cursor) has a
        location to work from.
        \"\"\"
--------------------------------------------------------------------------
"""

import cv2
import numpy as np
from hand_tracker import get_hand_state
from calibration import calibrate
from gestures import GestureController

SURFACE_W, SURFACE_H = 1280, 720   # output "whiteboard" resolution
ERASE_RADIUS = 30                  # pixels, in surface space
DRAW_RADIUS = 4                    # line thickness, in surface space
GESTURE_COOLDOWN_FRAMES = 15       # debounce for one-shot gesture triggers
RECALIBRATE_KEY = ord('r')         # keyboard-ONLY -- see note below

INK_COLOR = (0, 0, 0)               # black, BGR
BACKGROUND_COLOR = (255, 255, 255)  # white, BGR

# Cursor indicator -- shows where the tracked point currently maps to
# on the surface, regardless of gesture, so the user always knows
# where a stroke or erase would land before committing to it. Colored
# to stay visible against both the white background and black ink.
CURSOR_RADIUS = 8
CURSOR_COLOR_HOVER = (180, 180, 180)  # light gray -- "open" gesture, no action
CURSOR_COLOR_DRAW = (0, 0, 255)       # red -- "point" gesture, drawing
CURSOR_COLOR_ERASE = (0, 140, 255)    # orange -- "fist" gesture, erasing;
                                        # drawn at ERASE_RADIUS to preview
                                        # the actual erase area


def _blank_canvas():
    canvas = np.empty((SURFACE_H, SURFACE_W, 3), dtype=np.uint8)
    canvas[:] = BACKGROUND_COLOR
    return canvas


# Recalibration is intentionally bound to a keyboard key and nothing
# else. There is no gesture that triggers it. A misread gesture (a
# "fist" misclassified from a "point", say) should never be able to
# blow away calibration -- or, since recalibrating doesn't touch
# ink_layer, the user's drawn work either. Keep it this way.


def main():
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)

    H = calibrate(cap, SURFACE_W, SURFACE_H)

    # Persistent ink layer in surface space -- strokes stay put frame to
    # frame. This IS the display -- a plain virtual canvas, not the
    # camera feed. See module docstring for why.
    ink_layer = _blank_canvas()
    gesture_ctrl = GestureController(cooldown_frames=GESTURE_COOLDOWN_FRAMES)
    prev_surface_pt = None  # used only while actively drawing (point gesture)

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        state = get_hand_state(frame)
        display_canvas = ink_layer.copy()  # cursor overlay goes here, never on ink_layer itself

        if state is not None:
            cam_pt = np.array([[state["position"]]], dtype=np.float32)
            surface_pt = cv2.perspectiveTransform(cam_pt, H)[0][0]
            sx, sy = int(surface_pt[0]), int(surface_pt[1])
            inside_surface = 0 <= sx < SURFACE_W and 0 <= sy < SURFACE_H

            _, gesture = gesture_ctrl.update(state["gesture"])

            if inside_surface and gesture == "point":
                if prev_surface_pt is not None:
                    cv2.line(ink_layer, prev_surface_pt, (sx, sy),
                              INK_COLOR, DRAW_RADIUS)
                prev_surface_pt = (sx, sy)
                cv2.circle(display_canvas, (sx, sy), CURSOR_RADIUS,
                           CURSOR_COLOR_DRAW, -1)

            elif inside_surface and gesture == "fist":
                cv2.circle(ink_layer, (sx, sy), ERASE_RADIUS, BACKGROUND_COLOR, -1)
                prev_surface_pt = None
                cv2.circle(display_canvas, (sx, sy), ERASE_RADIUS,
                           CURSOR_COLOR_ERASE, 2)

            else:
                prev_surface_pt = None
                if inside_surface:
                    cv2.circle(display_canvas, (sx, sy), CURSOR_RADIUS,
                               CURSOR_COLOR_HOVER, 2)
        else:
            gesture_ctrl.update(None)
            prev_surface_pt = None

        cv2.imshow("Whiteboard surface", display_canvas)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == RECALIBRATE_KEY:
            # Recompute H only. ink_layer is untouched, so anything
            # already drawn stays exactly where it is in surface space
            # -- only the camera-to-surface mapping is re-locked.
            H = calibrate(cap, SURFACE_W, SURFACE_H)
            prev_surface_pt = None
            gesture_ctrl.reset()

    cap.release()
    cv2.destroyAllWindows()
>>>>>>> ryanbranch


if __name__ == "__main__":
    main()
