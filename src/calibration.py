"""
Manual calibration: the user pinches at each of the 4 corners of their
drawing surface, in order (top-left, top-right, bottom-right,
bottom-left), to define the region that gets warped into "surface
space" for drawing.

Hardening in this version:
  - 'z' undoes the most recently placed corner (redo just one corner
    without starting over).
  - 'c' clears all placed corners and restarts calibration from
    scratch.
  - 'q' cancels calibration entirely (raises SystemExit).
  - After all 4 corners are placed, the resulting quadrilateral is
    validated (non-degenerate area, consistent winding / no
    self-intersection). If it fails validation, the user is shown why
    and calibration restarts automatically rather than silently
    producing a broken homography.

Deliberately NOT included: any gesture-based way to trigger a restart
or clear. Calibration corners are placed via pinch, but undo/restart
are keyboard-only. This is intentional -- a misclassified gesture
during normal use should never be able to wipe out calibration (and,
in main.py, never wipe out drawn work either).

Depends on:
  - hand_tracker.get_hand_state(frame) -- see main.py for the expected
    interface contract.
  - gestures.GestureController -- for pinch edge-detection, so briefly
    holding a pinch only registers one corner.
"""

import cv2
import numpy as np
from hand_tracker import get_hand_state
from gestures import GestureController

CORNER_LABELS = ["TOP-LEFT", "TOP-RIGHT", "BOTTOM-RIGHT", "BOTTOM-LEFT"]
MIN_QUAD_AREA = 2000  # px^2, in camera space -- guards against a degenerate/collapsed quad


def _quad_area(corners):
    """Shoelace formula. Returns a signed area (sign encodes winding direction)."""
    area = 0.0
    n = len(corners)
    for i in range(n):
        x1, y1 = corners[i]
        x2, y2 = corners[(i + 1) % n]
        area += (x1 * y2) - (x2 * y1)
    return area / 2.0


def _is_convex_and_simple(corners):
    """
    Checks that consecutive edges all turn the same direction (all cross
    products share a sign). For 4 points this is sufficient to rule out
    a self-intersecting ("bowtie") quad and non-convex shapes, which
    would otherwise produce a nonsensical or unstable homography.
    """
    n = len(corners)
    signs = []
    for i in range(n):
        ax, ay = corners[i]
        bx, by = corners[(i + 1) % n]
        cx, cy = corners[(i + 2) % n]
        v1 = (bx - ax, by - ay)
        v2 = (cx - bx, cy - by)
        cross = v1[0] * v2[1] - v1[1] * v2[0]
        signs.append(cross > 0)
    return all(signs) or not any(signs)  # all same sign, either direction


def _validate_quad(corners):
    """
    Returns (is_valid, reason). reason is a short human-readable string
    explaining failure, used for on-screen feedback.
    """
    area = abs(_quad_area(corners))
    if area < MIN_QUAD_AREA:
        return False, "Corners are too close together / collapsed"
    if not _is_convex_and_simple(corners):
        return False, "Corners don't form a simple quad (crossed or non-convex)"
    return True, ""


def calibrate_with_finger(cap, surface_w, surface_h, cooldown_frames=15):
    corners = []
    gesture_ctrl = GestureController(cooldown_frames=cooldown_frames)
    status_msg = ""
    status_msg_ttl = 0  # frames remaining to show status_msg

    cv2.namedWindow("Calibration")

    while True:
        ret, frame = cap.read()
        if not ret:
            continue

        state = get_hand_state(frame)
        display = frame.copy()

        if len(corners) < 4:
            cv2.putText(display, f"Pinch at: {CORNER_LABELS[len(corners)]}",
                        (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 255), 2)
        cv2.putText(display, "Z: undo last  |  C: restart all  |  Q: cancel",
                    (20, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (200, 200, 200), 1)

        if status_msg_ttl > 0:
            cv2.putText(display, status_msg, (20, 100),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
            status_msg_ttl -= 1

        for i, pt in enumerate(corners):
            cv2.circle(display, pt, 6, (0, 255, 0), -1)
            cv2.putText(display, str(i + 1), (pt[0] + 8, pt[1] - 8),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        if len(corners) > 1:
            cv2.polylines(display, [np.array(corners, dtype=np.int32)],
                          isClosed=(len(corners) == 4), color=(0, 200, 0), thickness=1)

        if state is not None and len(corners) < 4:
            pos = state["position"]
            cv2.circle(display, pos, 8, (255, 0, 255), 2)
            is_new_trigger, gesture = gesture_ctrl.update(state["gesture"])
            if is_new_trigger and gesture == "pinch":
                corners.append(pos)
        else:
            gesture_ctrl.update(None if state is None else state["gesture"])

        cv2.imshow("Calibration", display)
        key = cv2.waitKey(1) & 0xFF

        if key == ord('q'):
            raise SystemExit("Calibration cancelled.")
        elif key == ord('z') and corners:
            corners.pop()
            status_msg, status_msg_ttl = "Last corner undone", 60
        elif key == ord('c') and corners:
            corners = []
            status_msg, status_msg_ttl = "Calibration restarted", 60

        if len(corners) == 4:
            is_valid, reason = _validate_quad(corners)
            if is_valid:
                break
            status_msg, status_msg_ttl = f"Invalid region ({reason}) -- restarting", 90
            corners = []

    cv2.destroyWindow("Calibration")

    src_pts = np.array(corners, dtype=np.float32)
    dst_pts = np.array([
        [0, 0],
        [surface_w - 1, 0],
        [surface_w - 1, surface_h - 1],
        [0, surface_h - 1],
    ], dtype=np.float32)

    H, _ = cv2.findHomography(src_pts, dst_pts)
    return H
