import cv2
import numpy as np

def fit_width(frame: np.ndarray, width: int) -> np.ndarray:
    """return frame scaled down to width, keeping aspect"""
    h, w = frame.shape[:2]
    if w <= width:
        return frame

    height = round(h * width / w)

    return cv2.resize(frame, (width, height), interpolation = cv2.INTER_AREA)

def to_rgb(frame: np.ndarray) -> np.ndarray:
    return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
