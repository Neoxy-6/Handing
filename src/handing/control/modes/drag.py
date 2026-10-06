import numpy as np

from handing.control.modes.mouse import MouseMode

class DragMode(MouseMode):
    """mouse mode with the left button held, released when the gesture ends"""

    def enter(self, point: np.ndarray, timestamp_ms: int) -> None:
        super().enter(point, timestamp_ms)
        self.mouse.press("left")

    def exit(self) -> None:
        self.mouse.release("left")
        super().exit()
