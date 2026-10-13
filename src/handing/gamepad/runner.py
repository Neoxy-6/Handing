from dataclasses import dataclass

import numpy as np

from handing.config.schema import Config
from handing.core.types import HandFrame
from handing.gamepad.mapping import Mapper, PadState
from handing.pipeline.capture import Capture
from handing.pipeline.dual import DualTracker, Side
from handing.recognition.classifier import Classifier
from handing.recognition.samples import SampleSet

@dataclass(frozen = True)
class GamepadTick:
    frame: np.ndarray  # bgr, resized to camera.width
    hands: HandFrame
    sides: dict[str, Side]
    pad: PadState  # what was sent, before the emergency stop

class GamepadRunner:
    """capture -> both hands -> mapping -> pad, one frame per step()"""

    def __init__(self, cfg: Config, pad, samples: SampleSet):
        self.cfg = cfg
        self.pad = pad
        self.capture = Capture(cfg, 2)

        rec = cfg.recognition
        self.classifier = Classifier(samples, rec.k, rec.max_distance, rec.align_rotation)
        self.tracker = DualTracker(cfg, self.classifier)
        self.rebuild_control()

    def rebuild_control(self) -> None:
        """apply changed gamepad settings"""
        self.mapper = Mapper(self.cfg)
        self.pad.release()

    def step(self) -> GamepadTick | None:
        """None when the camera gave no frame"""
        read = self.capture.read()
        if read is None:
            return None

        frame, hands = read
        sides = self.tracker.update(hands)
        if any(s.hand for s in sides.values()):
            self.capture.saw_hand()

        state = self.mapper.update(sides, hands.timestamp_ms)
        self.pad.send(state)

        return GamepadTick(frame, hands, sides, state)

    def open(self) -> None:
        self.capture.open()

    def close(self) -> None:
        self.pad.release()
        self.capture.close()

    def __enter__(self) -> "GamepadRunner":
        self.open()
        return self

    def __exit__(self, *_) -> None:
        self.close()
