from dataclasses import dataclass

import numpy as np

from handing.core.types import Body, Hand
from handing.filtering.one_euro import OneEuro
from handing.vr.arm import SIDES, ArmSize
from handing.vr.space import Space

WRIST, INDEX_MCP, MIDDLE_MCP, PINKY_MCP = 0, 5, 9, 17

@dataclass(frozen = True)
class ControllerPose:
    position: np.ndarray  # (3,) meters in room space
    rotation: np.ndarray  # (4,) quaternion x, y, z, w, identity looks forward with the palm down
    forward: np.ndarray  # (3,) where the fingers point
    up: np.ndarray  # (3,) out of the back of the hand
    tracked: bool  # false while the arm is not seen, the last pose is kept

def hand_axes(hand: Hand, space: Space) -> tuple[np.ndarray, np.ndarray]:
    """forward (wrist -> middle knuckle) and up (back of the hand) in room space, not yet orthogonal"""
    w = hand.world
    forward = space.direction(w[MIDDLE_MCP] - w[WRIST])
    across = space.direction(w[INDEX_MCP] - w[PINKY_MCP])
    up = np.cross(across, forward)  # mirror images, so the left hand needs the other sign
    if hand.handedness != "Right":
        up = -up

    return forward / (np.linalg.norm(forward) or 1), up / (np.linalg.norm(up) or 1)

def orthonormal(forward: np.ndarray, up: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """right, up, forward as unit vectors, forward wins"""
    f = forward / (np.linalg.norm(forward) or 1)
    u = up - np.dot(up, f) * f
    u = u / (np.linalg.norm(u) or 1)

    return np.cross(u, f), u, f

def quaternion(right: np.ndarray, up: np.ndarray, forward: np.ndarray) -> np.ndarray:
    """rotation whose x, y, z axes are right, up, forward, as x, y, z, w"""
    m = np.column_stack([right, up, forward])
    t = np.trace(m)
    if t > 0:
        s = np.sqrt(t + 1) * 2
        q = [(m[2, 1] - m[1, 2]) / s, (m[0, 2] - m[2, 0]) / s, (m[1, 0] - m[0, 1]) / s, s / 4]
    else:
        i = int(np.argmax(np.diag(m)))
        j, k = (i + 1) % 3, (i + 2) % 3
        s = np.sqrt(m[i, i] - m[j, j] - m[k, k] + 1) * 2
        q = [0.0] * 4
        q[i] = s / 4
        q[j] = (m[j, i] + m[i, j]) / s
        q[k] = (m[k, i] + m[i, k]) / s
        q[3] = (m[k, j] - m[j, k]) / s

    q = np.array(q)

    return q / np.linalg.norm(q)

class PoseTracker:
    """arm reach and hand shape -> one smoothed controller pose per side"""

    def __init__(self, space: Space, sizes: dict[str, ArmSize]):
        self.space = space
        self.sizes = sizes
        self.position = {s: OneEuro(min_cutoff = 1.0, beta = 1.0) for s in SIDES}
        self.axes = {s: OneEuro(min_cutoff = 1.0, beta = 0.5) for s in SIDES}
        self.poses = {s: ControllerPose(np.zeros(3), np.array([0, 0, 0, 1.0]), np.array([0, 0, 1.0]), np.array([0, 1.0, 0]), False) for s in SIDES}

    def update(self, body: Body, hands: dict[str, Hand | None], reach: dict[str, float]) -> dict[str, ControllerPose]:
        for side in SIDES:
            self.poses[side] = self._side(side, body, hands.get(side), reach[side])

        return dict(self.poses)

    def _side(self, side: str, body: Body, hand: Hand | None, reach: float) -> ControllerPose:
        last = self.poses[side]
        arm = body.arms.get(side)
        if arm is None or not arm.seen():
            return ControllerPose(last.position, last.rotation, last.forward, last.up, False)

        size = self.sizes[side]
        forward_m = reach * (size.upper + size.fore) * self.space.shoulder_width
        raw = self.space.position(body, arm.points[2], forward_m)
        if raw is None:
            return ControllerPose(last.position, last.rotation, last.forward, last.up, False)

        position = self.position[side].update(raw, body.timestamp_ms)
        f, u = (last.forward, last.up) if hand is None else hand_axes(hand, self.space)
        smooth = self.axes[side].update(np.concatenate([f, u]), body.timestamp_ms)
        r, u, f = orthonormal(smooth[:3], smooth[3:])

        return ControllerPose(position, quaternion(r, u, f), f, u, True)
