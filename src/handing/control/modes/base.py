import numpy as np

class Mode:
    """point: tracking point in camera pixels, x grows toward the user's right"""

    def enter(self, point: np.ndarray, timestamp_ms: int) -> None:
        """first frame only records the position, so switching gestures never jumps"""

    def update(self, point: np.ndarray, timestamp_ms: int) -> None:
        pass

    def exit(self) -> None:
        """release anything still held"""
