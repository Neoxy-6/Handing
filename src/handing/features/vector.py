import numpy as np

from handing.core.types import Hand
from handing.features.align import align_rotation
from handing.features.geometry import joint_bends, tip_distances
from handing.features.normalize import normalize

SIZE = 20 * 3 + 10 + 15

def from_pose(pose: np.ndarray, align: bool = False) -> np.ndarray:
    """pose from normalize(), wrist dropped since it is always 0; align ignores how the hand is turned"""
    if align:
        pose = align_rotation(pose)

    return np.concatenate([pose[1:].ravel(), tip_distances(pose), joint_bends(pose)]).astype(np.float32)

def from_hand(hand: Hand, width: int, height: int, align: bool = False) -> np.ndarray:
    return from_pose(normalize(hand, width, height), align)
