"""
Hand tracking + gesture classification, built on MediaPipe's
HandLandmarker (Tasks API).

NOTE ON MEDIAPIPE VERSION: MediaPipe has moved from the older
`mp.solutions.hands` API to the newer Tasks API (`mediapipe.tasks`).
Recent pip builds (this was written/tested against mediapipe 0.10.33)
no longer ship `mp.solutions` at all -- only Tasks. This file uses
Tasks throughout. If you're on an older mediapipe version where
`mp.solutions.hands` still works, both approaches give you the same
21 hand landmarks; this one is the actively-maintained path going
forward.

Implements the interface contract used throughout the rest of the
project (calibration.py, main.py):

    get_hand_state(frame) -> dict | None

    Returns None if no hand is detected, otherwise:
        {
            "position": (x, y),   # int pixel coords in CAMERA space --
                                   # the index fingertip
            "gesture":  "point" | "fist" | "open"
        }

Gesture logic:
  - "point": index finger extended, middle/ring/pinky curled -- a
    deliberate pointing pose. Triggers DRAW.
  - "fist": all four non-thumb fingers curled. Triggers ERASE.
  - "open": anything else (relaxed open hand, etc). This is the
    neutral/hover state -- no drawing or erasing happens, which is
    what lets the user move their hand over the surface without
    leaving a trail. Deliberately NOT a catch-all that includes
    "point" -- point is checked explicitly against its own curl
    pattern, so an open hand can't accidentally register as drawing.

"Curled" is determined per-finger via distance-from-wrist (tip closer
to wrist than that finger's MCP joint = curled), which is
rotation-invariant, unlike a raw y-coordinate comparison.

(Earlier versions of this file also detected a "pinch" gesture for
drawing. It was dropped in favor of "point" -- pinch requires precise
thumb-index proximity that proved noisier/harder to hold steadily
than a simple extended-index pose.)

MODEL FILE: HandLandmarker needs a .task model file. On first run,
this module downloads it automatically to ./models/hand_landmarker.task
if not already present (requires internet access for that one-time
download). If your environment has no internet access at runtime,
download it yourself ahead of time from:
    https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task
and place it at MODEL_PATH below.

Run this file directly (`python hand_tracker.py`) for a standalone
visual test -- shows the camera feed with detected landmarks,
fingertip position, and current gesture label, independent of
calibration.py/main.py. Useful for tuning PINCH_THRESHOLD_RATIO or
CURL_MARGIN against your own hand/lighting before running the full app.
"""

import math
import os
import ssl
import time
import urllib.request
from urllib.error import URLError

import cv2
import mediapipe as mp
from mediapipe.tasks.python import vision
from mediapipe.tasks.python.core.base_options import BaseOptions

MODEL_PATH = os.path.join(os.path.dirname(__file__), "models", "hand_landmarker.task")
MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/hand_landmarker/"
    "hand_landmarker/float16/latest/hand_landmarker.task"
)

# Landmark indices (MediaPipe Hands convention -- unchanged from the
# legacy solutions API, same 21-point layout)
WRIST = 0
INDEX_MCP = 5
INDEX_TIP = 8
MIDDLE_MCP = 9
MIDDLE_TIP = 12
RING_MCP = 13
RING_TIP = 16
PINKY_MCP = 17
PINKY_TIP = 20

# Tuning knob -- adjust against your own camera/hand if fist/point
# detection feels too sensitive or not sensitive enough.
CURL_MARGIN = 0.9  # a finger counts as curled if tip-to-wrist distance
                    # < CURL_MARGIN * mcp-to-wrist distance


def _dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def _ensure_model_downloaded():
    if os.path.exists(MODEL_PATH):
        return
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    print(f"Downloading hand landmark model to {MODEL_PATH} ...")
    try:
        urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)
    except URLError as e:
        if not isinstance(e.reason, ssl.SSLCertVerificationError):
            raise
        # Common on macOS python.org installs: the interpreter has no
        # access to the system trust store, so ANY https request fails
        # verification, not just this one. Retry using certifi's cert
        # bundle if it's available, rather than making the user go fix
        # their Python install just to run this script.
        try:
            import certifi
        except ImportError:
            raise RuntimeError(
                "SSL certificate verification failed, and certifi isn't "
                "installed to fall back on. Either run 'pip install certifi' "
                "and retry, or (on macOS with python.org Python) run the "
                "'Install Certificates.command' script in your Python's "
                "Applications folder. Alternatively, download the model "
                f"manually from {MODEL_URL} and place it at {MODEL_PATH}."
            ) from e
        context = ssl.create_default_context(cafile=certifi.where())
        with urllib.request.urlopen(MODEL_URL, context=context) as response, \
                open(MODEL_PATH, "wb") as out_file:
            out_file.write(response.read())
    print("Done.")


class HandTracker:
    """
    Wraps a MediaPipe HandLandmarker instance. Kept as a class (rather
    than recreating the model every call) since model init is
    expensive -- instantiate once, call process_frame() every frame.

    Uses VIDEO running mode (vs. IMAGE) since we're feeding a
    continuous webcam stream -- this lets MediaPipe use the previous
    frame's result to track faster and more smoothly than treating
    every frame as an independent image. VIDEO mode requires
    monotonically increasing timestamps, which we track internally.
    """

    def __init__(self, num_hands=1, min_hand_detection_confidence=0.6,
                 min_tracking_confidence=0.6):
        _ensure_model_downloaded()

        options = vision.HandLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=MODEL_PATH),
            running_mode=vision.RunningMode.VIDEO,
            num_hands=num_hands,
            min_hand_detection_confidence=min_hand_detection_confidence,
            min_tracking_confidence=min_tracking_confidence,
        )
        self._landmarker = vision.HandLandmarker.create_from_options(options)
        self._start_time_ms = time.time() * 1000

    def _next_timestamp_ms(self):
        return int(time.time() * 1000 - self._start_time_ms)

    def process_frame(self, frame):
        """
        Runs detection on a single BGR frame. Returns (state, landmarks)
        where state matches the get_hand_state() contract (or None),
        and landmarks is the raw list of (x, y) pixel points for the
        detected hand (or None) -- exposed for the standalone visual
        test below.
        """
        h, w = frame.shape[:2]
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)

        result = self._landmarker.detect_for_video(mp_image, self._next_timestamp_ms())

        if not result.hand_landmarks:
            return None, None

        hand = result.hand_landmarks[0]  # first detected hand
        pts = [(lm.x * w, lm.y * h) for lm in hand]

        palm_size = _dist(pts[WRIST], pts[MIDDLE_MCP])
        if palm_size < 1e-3:
            return None, pts  # degenerate frame, treat as no detection

        def is_curled(tip_idx, mcp_idx):
            return _dist(pts[tip_idx], pts[WRIST]) < CURL_MARGIN * _dist(pts[mcp_idx], pts[WRIST])

        index_curled = is_curled(INDEX_TIP, INDEX_MCP)
        middle_curled = is_curled(MIDDLE_TIP, MIDDLE_MCP)
        ring_curled = is_curled(RING_TIP, RING_MCP)
        pinky_curled = is_curled(PINKY_TIP, PINKY_MCP)

        if index_curled and middle_curled and ring_curled and pinky_curled:
            gesture = "fist"
        elif (not index_curled) and middle_curled and ring_curled and pinky_curled:
            gesture = "point"
        else:
            gesture = "open"

        position = (int(pts[INDEX_TIP][0]), int(pts[INDEX_TIP][1]))
        return {"position": position, "gesture": gesture}, pts

    def close(self):
        self._landmarker.close()


# Module-level singleton + functional wrapper, so calibration.py and
# main.py can just do `from hand_tracker import get_hand_state` without
# managing a HandTracker instance themselves.
_tracker = None


def get_hand_state(frame):
    global _tracker
    if _tracker is None:
        _tracker = HandTracker()
    state, _ = _tracker.process_frame(frame)
    return state


# Hand connections for drawing a skeleton in the standalone test below
# (index pairs into the 21-point landmark list).
_HAND_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),          # thumb
    (0, 5), (5, 6), (6, 7), (7, 8),          # index
    (5, 9), (9, 10), (10, 11), (11, 12),     # middle
    (9, 13), (13, 14), (14, 15), (15, 16),   # ring
    (13, 17), (17, 18), (18, 19), (19, 20),  # pinky
    (0, 17),
]


if __name__ == "__main__":
    # Standalone visual test: shows landmarks, fingertip position, and
    # the classified gesture, independent of calibration.py/main.py.
    tracker = HandTracker()
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)

    print("Press 'q' to quit.")
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frame = cv2.flip(frame, 1)  # mirror for a more natural test view

        state, pts = tracker.process_frame(frame)

        if pts is not None:
            for a, b in _HAND_CONNECTIONS:
                pa = (int(pts[a][0]), int(pts[a][1]))
                pb = (int(pts[b][0]), int(pts[b][1]))
                cv2.line(frame, pa, pb, (0, 200, 0), 2)
            for x, y in pts:
                cv2.circle(frame, (int(x), int(y)), 3, (0, 255, 255), -1)

        if state is not None:
            cv2.circle(frame, state["position"], 10, (255, 0, 255), -1)
            cv2.putText(frame, state["gesture"].upper(), (20, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2)
        else:
            cv2.putText(frame, "NO HAND", (20, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 2)

        cv2.imshow("hand_tracker.py standalone test", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    tracker.close()
    cap.release()
    cv2.destroyAllWindows()
