from pathlib import Path

import numpy as np

from handing.core.types import Hand, HandFrame

def load(path: Path) -> list[HandFrame]:
    """inverse of recorder.save"""
    data = np.load(path)
    grouped: list[list[Hand]] = [[] for _ in data["timestamp_ms"]]

    for i, lms, world, side, score in zip(
        data["frame_index"], data["landmarks"], data["world"], data["handedness"], data["score"]
    ):
        grouped[i].append(Hand(lms, world, str(side), float(score)))

    return [
        HandFrame(int(t), int(w), int(h), tuple(hands))
        for t, (w, h), hands in zip(data["timestamp_ms"], data["size"], grouped)
    ]

def latest(folder: Path) -> Path | None:
    files = sorted(folder.glob("*.npz"))

    return files[-1] if files else None
