import numpy as np

class KNN:
    def __init__(self, k: int = 5):
        self.k = k
        self._x = np.zeros((0, 0), np.float32)
        self._ids = np.zeros(0, np.int64)
        self.classes = np.zeros(0, dtype = "U1")

    def fit(self, x: np.ndarray, labels: np.ndarray) -> None:
        """no training, just keep the samples"""
        self._x = np.asarray(x, np.float32)
        self._sq = (self._x ** 2).sum(axis = 1)
        self.classes, self._ids = np.unique(labels, return_inverse = True)

    def query(self, x: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """x (n, d); return labels, vote ratio, mean distance to the winning neighbors"""
        x = np.atleast_2d(np.asarray(x, np.float32))
        n, k = len(x), min(self.k, len(self._x))
        rows = np.arange(n)[:, None]

        d2 = (x ** 2).sum(axis = 1)[:, None] + self._sq - 2 * x @ self._x.T
        near = np.argpartition(d2, k - 1, axis = 1)[:, :k]
        near_ids = self._ids[near]
        near_dist = np.sqrt(np.maximum(d2[rows, near], 0))

        votes = np.zeros((n, len(self.classes)), np.int64)
        np.add.at(votes, (np.repeat(rows, k, axis = 1), near_ids), 1)
        winner = votes.argmax(axis = 1)

        hit = near_ids == winner[:, None]
        dist = (near_dist * hit).sum(axis = 1) / hit.sum(axis = 1)

        return self.classes[winner], votes[rows[:, 0], winner] / k, dist
