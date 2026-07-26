"""
Entry point: calibrate the drawing surface with a finger-pinch, then
run the live draw/erase loop constrained to that surface.

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
                "gesture":  "pinch"   # thumb+index pinched together -> DRAW
                          | "fist"    # closed fist                  -> ERASE
                          | "point"   # anything else (open hand,
                                      #  pointing, etc.)              -> MOVE
            }

        "position" should be returned regardless of gesture -- i.e. even
        during a fist, still report a representative point (e.g. index
        MCP or palm centroid) so erasing has a location to work from.
        \"\"\"
--------------------------------------------------------------------------
"""

import cv2
import numpy as np
from hand_tracker import get_hand_state
from calibration import calibrate_with_finger
from gestures import GestureController

SURFACE_W, SURFACE_H = 1280, 720   # output "whiteboard" resolution
ERASE_RADIUS = 30                  # pixels, in surface space
DRAW_RADIUS = 4                    # line thickness, in surface space
GESTURE_COOLDOWN_FRAMES = 15       # debounce for one-shot gesture triggers
RECALIBRATE_KEY = ord('r')         # keyboard-ONLY -- see note below

# Recalibration is intentionally bound to a keyboard key and nothing
# else. There is no gesture that triggers it. A misread gesture (a
# "fist" misclassified from a "pinch", say) should never be able to
# blow away calibration -- or, since recalibrating doesn't touch
# ink_layer, the user's drawn work either. Keep it this way.


def main():
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)

    H = calibrate_with_finger(cap, SURFACE_W, SURFACE_H, GESTURE_COOLDOWN_FRAMES)

    # Persistent ink layer in surface space -- strokes stay put frame to
    # frame, and erasing just paints black (or your background color)
    # back into this layer.
    ink_layer = np.zeros((SURFACE_H, SURFACE_W, 3), dtype=np.uint8)
    gesture_ctrl = GestureController(cooldown_frames=GESTURE_COOLDOWN_FRAMES)
    prev_surface_pt = None  # used only while actively drawing (pinch)

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        warped_view = cv2.warpPerspective(frame, H, (SURFACE_W, SURFACE_H))
        state = get_hand_state(frame)

        if state is not None:
            cam_pt = np.array([[state["position"]]], dtype=np.float32)
            surface_pt = cv2.perspectiveTransform(cam_pt, H)[0][0]
            sx, sy = int(surface_pt[0]), int(surface_pt[1])
            inside_surface = 0 <= sx < SURFACE_W and 0 <= sy < SURFACE_H

            _, gesture = gesture_ctrl.update(state["gesture"])

            if inside_surface and gesture == "pinch":
                if prev_surface_pt is not None:
                    cv2.line(ink_layer, prev_surface_pt, (sx, sy),
                              (0, 0, 255), DRAW_RADIUS)
                prev_surface_pt = (sx, sy)

            elif inside_surface and gesture == "fist":
                cv2.circle(ink_layer, (sx, sy), ERASE_RADIUS, (0, 0, 0), -1)
                prev_surface_pt = None

            else:
                prev_surface_pt = None
        else:
            gesture_ctrl.update(None)
            prev_surface_pt = None

        combined = cv2.addWeighted(warped_view, 1.0, ink_layer, 1.0, 0)
        cv2.imshow("Whiteboard surface", combined)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == RECALIBRATE_KEY:
            # Recompute H only. ink_layer is untouched, so anything
            # already drawn stays exactly where it is in surface space
            # -- only the camera-to-surface mapping is re-locked.
            H = calibrate_with_finger(cap, SURFACE_W, SURFACE_H, GESTURE_COOLDOWN_FRAMES)
            prev_surface_pt = None
            gesture_ctrl.reset()

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
