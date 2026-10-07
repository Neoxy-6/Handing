import numpy as np

from handing.features.normalize import MIDDLE_MCP

def align_rotation(pose: np.ndarray) -> np.ndarray:
    """turn the pose in the image plane so wrist -> middle finger root points straight up"""
    v = pose[MIDDLE_MCP, 0] + 1j * pose[MIDDLE_MCP, 1]
    if abs(v) < 1e-9:
        return pose

    turn = -1j / (v / abs(v))  # up is -y in image coords
    xy = (pose[:, 0] + 1j * pose[:, 1]) * turn

    out = pose.copy()
    out[:, 0], out[:, 1] = xy.real, xy.imag

    return out
