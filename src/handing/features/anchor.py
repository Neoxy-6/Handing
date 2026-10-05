import numpy as np

from handing.core.types import Hand

PALM = [0, 5, 9, 13, 17]  # wrist + four finger roots
INDEX_TIP = 8

def palm_center(hand: Hand) -> np.ndarray:
    """return (2,) normalized image coords"""
    return hand.landmarks[PALM, :2].mean(axis = 0)

def index_tip(hand: Hand) -> np.ndarray:
    return hand.landmarks[INDEX_TIP, :2].copy()
