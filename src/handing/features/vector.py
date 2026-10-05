import numpy as np

from handing.core.types import Hand
from handing.features.geometry import joint_bends, tip_distances
from handing.features.normalize import normalize

SIZE = 20 * 3 + 10 + 15

def from_pose(pose: np.ndarray) -> np.ndarray:
    """pose from normalize(), wrist dropped since it is always 0"""
    return np.concatenate([pose[1:].ravel(), tip_distances(pose), joint_bends(pose)]).astype(np.float32)

def from_hand(hand: Hand, width: int, height: int) -> np.ndarray:
    return from_pose(normalize(hand, width, height))
