from pathlib import Path

import numpy as np

from handing.core.types import HandFrame

class Recorder:
    def __init__(self):
        self.frames: list[HandFrame] = []
        self.active = False

    def start(self) -> None:
        self.frames = []
        self.active = True

    def add(self, frame: HandFrame) -> None:
        if self.active:
            self.frames.append(frame)

    def stop(self) -> list[HandFrame]:
        self.active = False

        return self.frames

def save(frames: list[HandFrame], path: Path) -> None:
    """flatten hands so frames with 0..n hands fit in fixed arrays"""
    hands = [(i, hand) for i, f in enumerate(frames) for hand in f.hands]

    np.savez_compressed(
        path,
        timestamp_ms = np.array([f.timestamp_ms for f in frames], dtype = np.int64),
        size = np.array([(f.width, f.height) for f in frames], dtype = np.int32).reshape(-1, 2),
        frame_index = np.array([i for i, _ in hands], dtype = np.int32),
        landmarks = np.array([h.landmarks for _, h in hands], dtype = np.float32).reshape(-1, 21, 3),
        world = np.array([h.world for _, h in hands], dtype = np.float32).reshape(-1, 21, 3),
        handedness = np.array([h.handedness for _, h in hands], dtype = "U5"),
        score = np.array([h.score for _, h in hands], dtype = np.float32),
    )
