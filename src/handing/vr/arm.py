from dataclasses import dataclass

import numpy as np

from handing.core.types import Body
from handing.filtering.one_euro import OneEuro

SIDES = ("left", "right")

@dataclass(frozen = True)
class ArmSize:
    upper: float  # shoulder -> elbow, in shoulder widths
    fore: float  # elbow -> wrist, in shoulder widths

def segments(body: Body, side: str) -> tuple[float, float] | None:
    """upper arm and forearm as seen in the picture, in shoulder widths, None when not fully seen"""
    if len(body.arms) < 2 or not all(arm.seen() for arm in body.arms.values()):
        return None

    scale = np.array([body.width, body.height], np.float32)
    shoulders = [body.arms[s].points[0] * scale for s in SIDES]
    width = float(np.linalg.norm(shoulders[0] - shoulders[1]))
    if width < 1:
        return None

    s, e, w = body.arms[side].points * scale

    return float(np.linalg.norm(e - s)) / width, float(np.linalg.norm(w - e)) / width

def reach(seen: tuple[float, float], size: ArmSize) -> float:
    """0 arm flat in the picture, 1 pointing straight at the camera, a shorter looking segment points more forward"""
    def depth(length: float, visible: float) -> float:
        return float(np.sqrt(max(length ** 2 - visible ** 2, 0.0)))

    return (depth(size.upper, seen[0]) + depth(size.fore, seen[1])) / (size.upper + size.fore)

class Calibration:
    """collects both arms while the user holds them out sideways, foreshortening only shortens, so a high percentile is the real length"""

    def __init__(self, frames: int = 60):
        self.frames = frames
        self.samples: dict[str, list[tuple[float, float]]] = {s: [] for s in SIDES}

    def add(self, body: Body) -> None:
        for side in SIDES:
            seen = segments(body, side)
            if seen:
                self.samples[side].append(seen)

    @property
    def progress(self) -> float:
        return min(len(v) for v in self.samples.values()) / self.frames

    @property
    def done(self) -> bool:
        return self.progress >= 1

    def result(self) -> dict[str, ArmSize]:
        sizes = {}
        for side, rows in self.samples.items():
            upper, fore = np.percentile(np.array(rows), 90, axis = 0)
            sizes[side] = ArmSize(float(upper), float(fore))

        return sizes

class Reach:
    """smoothed reach per arm, keeps the last value while an arm is not seen"""

    def __init__(self, sizes: dict[str, ArmSize]):
        self.sizes = sizes
        self.filters = {s: OneEuro(min_cutoff = 1.0, beta = 2.0) for s in SIDES}
        self.values = {s: 0.0 for s in SIDES}

    def update(self, body: Body) -> dict[str, float]:
        for side in SIDES:
            seen = segments(body, side)
            if seen:
                raw = reach(seen, self.sizes[side])
                self.values[side] = float(self.filters[side].update(np.array([raw]), body.timestamp_ms)[0])

        return dict(self.values)
