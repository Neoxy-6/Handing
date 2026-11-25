from dataclasses import dataclass

import numpy as np

@dataclass(frozen = True)
class Hand:
    landmarks: np.ndarray  # (21, 3) normalized image coords
    world: np.ndarray  # (21, 3) meters, origin near hand center
    handedness: str  # "Left" or "Right", the real hand
    score: float
    chirality: str = ""  # which hand it looks like in this frame, differs from handedness when the frame is mirrored

    @property
    def looks_left(self) -> bool:
        return (self.chirality or self.handedness) == "Left"

@dataclass(frozen = True)
class HandFrame:
    timestamp_ms: int
    width: int
    height: int
    hands: tuple[Hand, ...] = ()

    @property
    def empty(self) -> bool:
        return not self.hands

@dataclass(frozen = True)
class Arm:
    points: np.ndarray  # (3, 2) normalized image coords: shoulder, elbow, wrist
    world: np.ndarray  # (3, 3) meters, origin between the hips
    visibility: np.ndarray  # (3,) 0..1, low when off screen or hidden

    def seen(self, min_visibility: float = 0.5) -> bool:
        return bool((self.visibility >= min_visibility).all())

@dataclass(frozen = True)
class Body:
    timestamp_ms: int
    width: int
    height: int
    arms: dict[str, Arm]  # "left" / "right", the real arm, empty without a person
