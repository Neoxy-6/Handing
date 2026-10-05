import numpy as np

from handing.core.types import Hand

WRIST = 0
MIDDLE_MCP = 9

def normalize(hand: Hand, width: int, height: int) -> np.ndarray:
    """return (21, 3) pose: wrist at origin, palm length 1, left hand mirrored to right"""
    pts = hand.landmarks * (width, height, width)  # back to square pixels, z shares x scale
    pts = pts - pts[WRIST]

    palm = np.linalg.norm(pts[MIDDLE_MCP])
    if palm < 1e-6:
        return np.zeros_like(pts)

    pts = pts / palm

    # left hand
    if hand.handedness == "Left":
        pts[:, 0] *= -1

    return pts
