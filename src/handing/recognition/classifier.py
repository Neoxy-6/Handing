from dataclasses import dataclass

import numpy as np

from handing.core.types import Hand
from handing.features import vector
from handing.recognition.knn import KNN
from handing.recognition.samples import SampleSet

UNKNOWN = "unknown"

@dataclass(frozen = True)
class Prediction:
    name: str
    confidence: float  # vote ratio of the k neighbors
    distance: float  # mean distance to the winning neighbors

class Classifier:
    def __init__(self, samples: SampleSet, k: int = 5, max_distance: float = 2.0):
        self.max_distance = max_distance
        self._knn = KNN(k)
        self.update(samples)

    def update(self, samples: SampleSet) -> None:
        """call after samples change, takes effect immediately"""
        poses, labels = samples.arrays()
        self._size = len(labels)

        if self._size:
            self._knn.fit(np.array([vector.from_pose(p) for p in poses]), labels)

    def predict(self, hand: Hand, width: int, height: int) -> Prediction:
        if not self._size:
            return Prediction(UNKNOWN, 0.0, float("inf"))

        names, ratios, dists = self._knn.query(vector.from_hand(hand, width, height))
        name, ratio, dist = str(names[0]), float(ratios[0]), float(dists[0])

        if dist > self.max_distance:
            name = UNKNOWN

        return Prediction(name, ratio, dist)
