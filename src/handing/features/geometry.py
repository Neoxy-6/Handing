from itertools import combinations

import numpy as np

TIPS = (4, 8, 12, 16, 20)
TIP_PAIRS = np.array(list(combinations(TIPS, 2)))

# wrist + 4 joints per finger: thumb, index, middle, ring, pinky
CHAINS = [(0, 1, 2, 3, 4), (0, 5, 6, 7, 8), (0, 9, 10, 11, 12), (0, 13, 14, 15, 16), (0, 17, 18, 19, 20)]
JOINTS = np.array([c[i:i + 3] for c in CHAINS for i in range(3)])  # (15, 3) prev, joint, next

def tip_distances(pose: np.ndarray) -> np.ndarray:
    """return (10,) distances between every pair of fingertips"""
    return np.linalg.norm(pose[TIP_PAIRS[:, 0]] - pose[TIP_PAIRS[:, 1]], axis = 1)

def joint_bends(pose: np.ndarray) -> np.ndarray:
    """return (15,) bend per joint in [0, 1], 0 = straight, 1 = folded back"""
    u = pose[JOINTS[:, 1]] - pose[JOINTS[:, 0]]
    v = pose[JOINTS[:, 2]] - pose[JOINTS[:, 1]]

    norms = np.linalg.norm(u, axis = 1) * np.linalg.norm(v, axis = 1)
    cos = np.einsum("ij,ij->i", u, v) / np.maximum(norms, 1e-9)

    return np.arccos(np.clip(cos, -1, 1)) / np.pi
