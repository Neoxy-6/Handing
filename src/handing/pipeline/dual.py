from dataclasses import dataclass

import numpy as np

from handing.config.keys import SIDES
from handing.config.schema import Config
from handing.core.types import Hand, HandFrame
from handing.features import anchor
from handing.filtering.hysteresis import Hysteresis
from handing.recognition.classifier import UNKNOWN, Classifier, Prediction

@dataclass(frozen = True)
class Side:
    hand: Hand | None
    prediction: Prediction | None  # before filtering
    gesture: str  # stable, UNKNOWN while the hand is away or unsure
    point: np.ndarray | None  # palm, camera px, x toward the user's right

class DualTracker:
    """both hands at once, each with its own filtering, keyed by the real hand"""

    def __init__(self, cfg: Config, classifier: Classifier):
        self.cfg = cfg
        self.classifier = classifier
        s = cfg.stability
        self.hyst = {side: Hysteresis(s.enter_frames, s.exit_frames, s.min_confidence) for side in SIDES}

    def update(self, hands: HandFrame) -> dict[str, Side]:
        return {side: self._side(side, hands) for side in SIDES}

    def _side(self, side: str, hands: HandFrame) -> Side:
        # mediapipe may label both hands the same, the second one is then ignored
        hand = next((h for h in hands.hands if h.handedness.lower() == side), None)
        if hand is None:
            self.hyst[side].reset()
            return Side(None, None, UNKNOWN, None)

        pred = self.classifier.predict(hand, hands.width, hands.height)
        gesture = self.hyst[side].update(pred.name, pred.confidence)
        point = anchor.control_point(hand, hands.width, hands.height, "palm", self.cfg.camera.frame_mirrored)

        return Side(hand, pred, gesture, point)
