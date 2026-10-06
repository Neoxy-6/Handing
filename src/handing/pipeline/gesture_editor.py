from pathlib import Path

import numpy as np

from handing.config import loader
from handing.config.schema import Config, GestureConfig
from handing.recognition.classifier import UNKNOWN
from handing.recognition.samples import SampleSet

def check_name(name: str, existing: list[str]) -> str | None:
    """return an error message, or None when the name is usable"""
    if not name.strip():
        return "name is empty"
    if name == UNKNOWN:
        return f"'{UNKNOWN}' is reserved"
    if name in existing:
        return f"'{name}' already exists"

    return None

class GestureEditor:
    """keeps samples and config in sync, saves both after every change"""

    def __init__(self, samples: SampleSet, cfg: Config, samples_path: Path):
        self.samples = samples
        self.cfg = cfg
        self.samples_path = samples_path

    def counts(self) -> dict[str, int]:
        return {name: self.samples.count(name) for name in self.samples.names}

    def add(self, name: str, poses: np.ndarray) -> None:
        self.samples.add(name, poses)
        self.samples.save(self.samples_path)

    def delete(self, name: str) -> None:
        self.samples.delete(name)
        self.cfg.gestures.pop(name, None)
        self._save()

    def rename(self, old: str, new: str) -> None:
        self.samples.rename(old, new)
        self.cfg.gestures = {new if k == old else k: v for k, v in self.cfg.gestures.items()}

        if self.cfg.safety.unlock_gesture == old:
            self.cfg.safety.unlock_gesture = new

        self._save()

    def set_gesture(self, name: str, gesture: GestureConfig | None) -> None:
        """None removes the mapping, the gesture is still recognized but does nothing"""
        if gesture is None:
            self.cfg.gestures.pop(name, None)
        else:
            self.cfg.gestures[name] = gesture

        loader.save(self.cfg)

    def _save(self) -> None:
        self.samples.save(self.samples_path)
        loader.save(self.cfg)
