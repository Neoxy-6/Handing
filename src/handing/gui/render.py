import cv2
import numpy as np
from mediapipe.tasks.python.vision import HandLandmarksConnections

from handing.core.types import Body, HandFrame

CONNECTIONS = [(c.start, c.end) for c in HandLandmarksConnections.HAND_CONNECTIONS]
LINE_COLOR = (0, 200, 0)
POINT_COLOR = (0, 0, 255)

def draw_skeleton(frame: np.ndarray, pts: np.ndarray) -> None:
    """pts: (21, 2) pixel coords"""
    pts = pts.astype(int)

    for a, b in CONNECTIONS:
        cv2.line(frame, tuple(pts[a]), tuple(pts[b]), LINE_COLOR, 2)

    for p in pts:
        cv2.circle(frame, tuple(p), 3, POINT_COLOR, -1)

def draw_hands(frame: np.ndarray, hand_frame: HandFrame) -> np.ndarray:
    """draw skeletons in place, and return a frame that has beendrawn"""
    h, w = frame.shape[:2]

    for hand in hand_frame.hands:
        pts = hand.landmarks[:, :2] * (w, h)
        draw_skeleton(frame, pts)

        x, y = pts[0].astype(int)
        cv2.putText(frame, hand.handedness, (x, y + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, LINE_COLOR, 1)

    return frame

ARM_COLOR = (255, 170, 40)
HIDDEN_COLOR = (90, 90, 90)  # joints the pose model is unsure about

def draw_arms(frame: np.ndarray, body: Body, min_visibility: float = 0.5) -> None:
    """shoulder -> elbow -> wrist per arm, grey where a joint is not seen"""
    h, w = frame.shape[:2]

    for side, arm in body.arms.items():
        pts = (arm.points * (w, h)).astype(int)
        seen = arm.visibility >= min_visibility

        for a, b in ((0, 1), (1, 2)):
            color = ARM_COLOR if seen[a] and seen[b] else HIDDEN_COLOR
            cv2.line(frame, tuple(pts[a]), tuple(pts[b]), color, 3, cv2.LINE_AA)

        for p, ok in zip(pts, seen):
            cv2.circle(frame, tuple(p), 5, ARM_COLOR if ok else HIDDEN_COLOR, -1)

        x, y = pts[0]
        cv2.putText(frame, side, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, ARM_COLOR, 1)

def draw_reach(frame: np.ndarray, values: dict[str, float]) -> None:
    """one bar per arm at the bottom, full when the arm points at the camera"""
    h, w = frame.shape[:2]
    bar_w = w // 2 - 30

    for i, (side, v) in enumerate(sorted(values.items())):
        x, y = 15 + i * (w // 2), h - 25
        cv2.rectangle(frame, (x, y), (x + bar_w, y + 12), HIDDEN_COLOR, 1)
        cv2.rectangle(frame, (x, y), (x + int(bar_w * min(max(v, 0), 1)), y + 12), ARM_COLOR, -1)
        cv2.putText(frame, f"{side} reach {v:.2f}", (x, y - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.5, ARM_COLOR, 1)

STICK_COLOR = (230, 160, 60)
IDLE_STICK_COLOR = (110, 90, 70)  # a gamepad stick nobody drives right now

def draw_stick(frame: np.ndarray, center: np.ndarray, radius: float, deadzone: float, hand_point: np.ndarray | None, color = STICK_COLOR) -> None:
    """joystick guide: outer ring, deadzone ring, line from the center to the hand"""
    c = tuple(center.astype(int))
    cv2.circle(frame, c, int(radius), color, 1, cv2.LINE_AA)
    cv2.circle(frame, c, max(int(radius * deadzone), 2), color, 1, cv2.LINE_AA)
    cv2.drawMarker(frame, c, color, cv2.MARKER_CROSS, 10, 1)

    if hand_point is not None:
        cv2.line(frame, c, tuple(hand_point.astype(int)), color, 2, cv2.LINE_AA)
