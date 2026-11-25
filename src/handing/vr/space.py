from dataclasses import dataclass

import numpy as np

from handing.core.types import Body

@dataclass(frozen = True)
class Space:
    """room space in meters: x the user's right, y up, z forward toward the camera, origin on the floor under the shoulders"""
    shoulder_width: float = 0.40  # the user's real shoulder width, sets the scale
    shoulder_height: float = 1.45  # shoulders above the floor
    mirrored: bool = True  # frame flipped, so picture right is the user's right

    def position(self, body: Body, point: np.ndarray, forward: float) -> np.ndarray | None:
        """point: normalized picture coords, forward: meters in front of the shoulders, None without both shoulders"""
        if len(body.arms) < 2:
            return None

        scale = np.array([body.width, body.height], np.float32)
        left, right = (body.arms[s].points[0] * scale for s in ("left", "right"))
        width = float(np.linalg.norm(left - right))
        if width < 1:
            return None

        dx, dy = (point * scale - (left + right) / 2) / width * self.shoulder_width

        return np.array([dx if self.mirrored else -dx, self.shoulder_height - dy, forward])

    def direction(self, v: np.ndarray) -> np.ndarray:
        """mediapipe world vector (x picture right, y down, z away from the camera) into room axes"""
        x, y, z = v

        return np.array([x if self.mirrored else -x, -y, -z])
