import numpy as np

from handing.config.schema import Config
from handing.core import paths
from handing.core.clock import now_ms
from handing.core.types import HandFrame
from handing.detection.landmarker import Landmarker
from handing.input import preprocess
from handing.input.camera import Camera
from handing.input.throttle import Throttle

class Capture:
    """camera -> throttle -> landmarks, shared by every runner"""

    def __init__(self, cfg: Config, num_hands: int):
        self.width = cfg.camera.width
        self.camera = Camera(cfg.camera.index, mirror = cfg.camera.flip)
        self.throttle = Throttle(cfg.camera.idle_fps)
        self.landmarker = Landmarker(paths.model_path(), num_hands, cfg.detection.min_confidence, cfg.camera.frame_mirrored)

    def read(self) -> tuple[np.ndarray, HandFrame] | None:
        """bgr frame resized to camera.width and its hands, None when the camera gave no frame"""
        self.throttle.wait()
        frame = self.camera.read()
        if frame is None:
            return None

        frame = preprocess.fit_width(frame, self.width)

        return frame, self.landmarker.detect(preprocess.to_rgb(frame), now_ms())

    def saw_hand(self) -> None:
        """keeps full speed, runners call it when a hand they use is in view"""
        self.throttle.saw_hand()

    def open(self) -> None:
        self.camera.open()

    def close(self) -> None:
        self.camera.close()
        self.landmarker.close()
