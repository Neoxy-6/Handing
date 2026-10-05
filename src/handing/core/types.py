from dataclasses import dataclass

import numpy as np

@dataclass(frozen = True)
class Hand:
    landmarks: np.ndarray  # (21, 3) normalized image coords
    world: np.ndarray  # (21, 3) meters, origin near hand center
    handedness: str  # "Left" or "Right"
    score: float

@dataclass(frozen = True)
class HandFrame:
    timestamp_ms: int
    width: int
    height: int
    hands: tuple[Hand, ...] = ()

    @property
    def empty(self) -> bool:
        return not self.hands
