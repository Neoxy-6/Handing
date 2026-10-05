from pathlib import Path

import numpy as np

class SampleSet:
    """gesture name -> normalized poses (n, 21, 3)"""

    def __init__(self):
        self._poses: dict[str, np.ndarray] = {}

    @property
    def names(self) -> list[str]:
        return list(self._poses)

    def count(self, name: str) -> int:
        return len(self._poses.get(name, ()))

    def add(self, name: str, poses: np.ndarray) -> None:
        poses = np.asarray(poses, dtype = np.float32).reshape(-1, 21, 3)
        if name in self._poses:
            poses = np.concatenate([self._poses[name], poses])

        self._poses[name] = poses

    def delete(self, name: str) -> None:
        self._poses.pop(name, None)

    def rename(self, old: str, new: str) -> None:
        if new in self._poses:
            raise ValueError(f"gesture '{new}' already exists")

        self._poses = {new if k == old else k: v for k, v in self._poses.items()}

    def arrays(self) -> tuple[np.ndarray, np.ndarray]:
        """return poses (N, 21, 3) and labels (N,)"""
        if not self._poses:
            return np.zeros((0, 21, 3), np.float32), np.zeros(0, dtype = "U1")

        poses = np.concatenate(list(self._poses.values()))
        labels = np.concatenate([[k] * len(v) for k, v in self._poses.items()])

        return poses, labels

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents = True, exist_ok = True)
        poses, labels = self.arrays()

        np.savez_compressed(path, poses = poses, labels = labels)

    @classmethod
    def load(cls, path: Path) -> "SampleSet":
        data = np.load(path)
        samples = cls()

        for name in dict.fromkeys(data["labels"]):
            samples.add(str(name), data["poses"][data["labels"] == name])

        return samples
