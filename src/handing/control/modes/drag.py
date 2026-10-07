import numpy as np

from handing.control.modes.base import Mode
from handing.output.mouse import Mouse

class DragMode(Mode):
    """runs a cursor mode with a mouse button held, released when the gesture ends"""

    def __init__(self, cursor: Mode, mouse: Mouse, button: str = "left"):
        self.cursor = cursor
        self.mouse = mouse
        self.button = button

    def enter(self, point: np.ndarray, timestamp_ms: int) -> None:
        self.cursor.enter(point, timestamp_ms)
        self.mouse.press(self.button)

    def update(self, point: np.ndarray, timestamp_ms: int) -> None:
        self.cursor.update(point, timestamp_ms)

    def exit(self) -> None:
        self.mouse.release(self.button)
        self.cursor.exit()
