import numpy as np

from handing.core.types import Hand

PALM = [0, 5, 9, 13, 17]  # wrist + four finger roots
INDEX_TIP = 8

def palm_center(hand: Hand) -> np.ndarray:
    """return (2,) normalized image coords"""
    return hand.landmarks[PALM, :2].mean(axis = 0)

def index_tip(hand: Hand) -> np.ndarray:
    return hand.landmarks[INDEX_TIP, :2].copy()

def of(hand: Hand, point: str) -> np.ndarray:
    """'palm' or 'index', see config POINTS"""
    return index_tip(hand) if point == "index" else palm_center(hand)

def control_point(hand: Hand, width: int, height: int, point: str, frame_mirrored: bool) -> np.ndarray:
    """camera px with x toward the user's right, a raw frame is flipped"""
    p = of(hand, point) * (width, height)
    if not frame_mirrored:
        p[0] = width - p[0]

    return p
