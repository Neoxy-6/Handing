import numpy as np

from handing.control.modes.base import Mode
from handing.output.mouse import Mouse

class DragMode(Mode):
    """runs a cursor mode with the left button held, released when the gesture ends"""

    def __init__(self, cursor: Mode, mouse: Mouse):
        self.cursor = cursor
        self.mouse = mouse

    def enter(self, point: np.ndarray, timestamp_ms: int) -> None:
        self.cursor.enter(point, timestamp_ms)
        self.mouse.press("left")

    def update(self, point: np.ndarray, timestamp_ms: int) -> None:
        self.cursor.update(point, timestamp_ms)

    def exit(self) -> None:
        self.mouse.release("left")
        self.cursor.exit()
