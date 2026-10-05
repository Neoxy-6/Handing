from pathlib import Path

import mediapipe as mp
import numpy as np
from mediapipe.tasks.python import BaseOptions, vision

from handing.core.types import Hand, HandFrame

SWAP = {"Left": "Right", "Right": "Left"}

class Landmarker:
    def __init__(self, model_path: Path, num_hands: int = 1, min_confidence: float = 0.5, mirrored = False):
        self.mirrored = mirrored  # mediapipe labels assume a raw, non-mirrored frame

        options = vision.HandLandmarkerOptions(
            base_options = BaseOptions(model_asset_path = str(model_path)),
            running_mode = vision.RunningMode.VIDEO,
            num_hands = num_hands,
            min_hand_detection_confidence = min_confidence,
            min_hand_presence_confidence = min_confidence,
            min_tracking_confidence = min_confidence,
        )
        self._task = vision.HandLandmarker.create_from_options(options)

    def detect(self, rgb: np.ndarray, timestamp_ms: int) -> HandFrame:
        """timestamps must increase between calls"""
        image = mp.Image(image_format = mp.ImageFormat.SRGB, data = rgb)
        result = self._task.detect_for_video(image, timestamp_ms)

        hands = tuple(
            _to_hand(lms, world, cats, self.mirrored)
            for lms, world, cats in zip(result.hand_landmarks, result.hand_world_landmarks, result.handedness)
        )
        h, w = rgb.shape[:2]

        return HandFrame(timestamp_ms, w, h, hands)

    def close(self) -> None:
        self._task.close()

    def __enter__(self) -> "Landmarker":
        return self

    def __exit__(self, *_) -> None:
        self.close()

def _to_hand(lms, world, cats, mirrored: bool) -> Hand:
    top = cats[0]
    handedness = SWAP[top.category_name] if mirrored else top.category_name

    return Hand(
        landmarks = np.array([(p.x, p.y, p.z) for p in lms], dtype = np.float32),
        world = np.array([(p.x, p.y, p.z) for p in world], dtype = np.float32),
        handedness = handedness,
        score = top.score,
    )
