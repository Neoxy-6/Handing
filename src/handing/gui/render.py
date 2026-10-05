import cv2
import numpy as np
from mediapipe.tasks.python.vision import HandLandmarksConnections

from handing.core.types import HandFrame

CONNECTIONS = [(c.start, c.end) for c in HandLandmarksConnections.HAND_CONNECTIONS]
LINE_COLOR = (0, 200, 0)
POINT_COLOR = (0, 0, 255)

def draw_hands(frame: np.ndarray, hand_frame: HandFrame) -> np.ndarray:
    """draw skeletons in place, and return a frame that has beendrawn"""
    h, w = frame.shape[:2]

    for hand in hand_frame.hands:
        pts = (hand.landmarks[:, :3] * (w, h)).astype(int)

        for a, b in CONNECTIONS:
            cv2.line(frame, tuple(pts[a]), tuple(pts[b]), LINE_COLOR, 2)

        for p in pts:
            cv2.circle(frame, tuple(p), 3, POINT_COLOR, -1)

        x, y = pts[0]
        cv2.putText(frame, hand.handedness, (x, y + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, LINE_COLOR, 1)

    return frame
