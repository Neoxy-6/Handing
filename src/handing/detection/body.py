from pathlib import Path

import mediapipe as mp
import numpy as np
from mediapipe.tasks.python import BaseOptions, vision

from handing.core.types import Arm, Body

ARMS = {"left": (11, 13, 15), "right": (12, 14, 16)}  # shoulder, elbow, wrist

class BodyLandmarker:
    """one person's arms from the pose model"""

    def __init__(self, model_path: Path, min_confidence: float = 0.5, mirrored = False):
        self.mirrored = mirrored  # like hands, pose labels assume a raw, non-mirrored frame

        options = vision.PoseLandmarkerOptions(
            base_options = BaseOptions(model_asset_path = str(model_path)),
            running_mode = vision.RunningMode.VIDEO,
            num_poses = 1,
            min_pose_detection_confidence = min_confidence,
            min_pose_presence_confidence = min_confidence,
            min_tracking_confidence = min_confidence,
        )
        self._task = vision.PoseLandmarker.create_from_options(options)

    def detect(self, rgb: np.ndarray, timestamp_ms: int) -> Body:
        """timestamps must increase between calls"""
        image = mp.Image(image_format = mp.ImageFormat.SRGB, data = rgb)
        result = self._task.detect_for_video(image, timestamp_ms)
        if not result.pose_landmarks:
            return Body(timestamp_ms, {})

        lms, world = result.pose_landmarks[0], result.pose_world_landmarks[0]
        arms = {side: _to_arm(lms, world, ids) for side, ids in ARMS.items()}
        if self.mirrored:
            arms = {"left": arms["right"], "right": arms["left"]}

        return Body(timestamp_ms, arms)

    def close(self) -> None:
        self._task.close()

    def __enter__(self) -> "BodyLandmarker":
        return self

    def __exit__(self, *_) -> None:
        self.close()

def _to_arm(lms, world, ids) -> Arm:
    return Arm(
        points = np.array([(lms[i].x, lms[i].y) for i in ids], dtype = np.float32),
        world = np.array([(world[i].x, world[i].y, world[i].z) for i in ids], dtype = np.float32),
        visibility = np.array([1.0 if lms[i].visibility is None else lms[i].visibility for i in ids], dtype = np.float32),
    )
