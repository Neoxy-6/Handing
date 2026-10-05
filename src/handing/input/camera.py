import sys

import cv2
import numpy as np

BACKEND = cv2.CAP_DSHOW if sys.platform == "win32" else cv2.CAP_ANY

class Camera:
    def __init__(self, index: int = 0, width: int = 640, height: int = 480, mirror = False):
        self.index = index
        self.width = width
        self.height = height
        self.mirror = mirror
        self._cap: cv2.VideoCapture | None = None

    def open(self) -> None:
        cap = cv2.VideoCapture(self.index, BACKEND)
        if not cap.isOpened():
            raise RuntimeError(f"cannot open camera {self.index}")
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        self._cap = cap

    def read(self) -> np.ndarray | None:
        """return bgr frame, or None on failure"""
        if self._cap is None:
            return None
        
        ok, frame = self._cap.read()

        if ok and self.mirror:
            return cv2.flip(frame, 1)

        return frame if ok else None

    def close(self) -> None:
        if self._cap is not None:
            self._cap.release()
            self._cap = None

    def __enter__(self) -> "Camera":
        self.open()
        return self

    def __exit__(self, *_) -> None:
        self.close()
