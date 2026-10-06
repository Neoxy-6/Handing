from dataclasses import dataclass

import numpy as np

from handing.features import vector
from handing.recognition.knn import KNN
from handing.recognition.samples import SampleSet

@dataclass(frozen = True)
class Similar:
    name: str  # existing gesture the new samples look like
    ratio: float  # share of new samples recognized as it
    distance: float  # median distance of those samples

def find_similar(samples: SampleSet, name: str, poses, k: int, max_distance: float, min_ratio: float = 0.5) -> Similar | None:
    """classify new poses against every other gesture, None when they stand apart"""
    others = samples.without(name)
    if not others.names or len(poses) == 0:
        return None

    known, labels = others.arrays()
    knn = KNN(k)
    knn.fit(np.array([vector.from_pose(p) for p in known]), labels)

    names, _, dist = knn.query(np.array([vector.from_pose(p) for p in poses]))
    hit = dist <= max_distance
    if not hit.any():
        return None

    found, counts = np.unique(names[hit], return_counts = True)
    best = int(counts.argmax())
    ratio = counts[best] / len(poses)

    if ratio < min_ratio:
        return None

    match = hit & (names == found[best])

    return Similar(str(found[best]), float(ratio), float(np.median(dist[match])))
