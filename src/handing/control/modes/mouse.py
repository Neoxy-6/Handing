import numpy as np

from handing.control.modes.base import Mode
from handing.filtering.one_euro import OneEuro
from handing.output.mouse import Mouse

class MouseMode(Mode):
    """relative: hand displacement times gain moves the cursor"""

    def __init__(self, mouse: Mouse, gain: float, deadzone: float, smoother: OneEuro):
        self.mouse = mouse
        self.gain = gain  # screen px per camera px
        self.deadzone = deadzone  # camera px per frame
        self.smoother = smoother
        self._last: np.ndarray | None = None

    def enter(self, point: np.ndarray, timestamp_ms: int) -> None:
        self.smoother.reset()
        self._last = self.smoother.update(point, timestamp_ms)

    def update(self, point: np.ndarray, timestamp_ms: int) -> None:
        p = self.smoother.update(point, timestamp_ms)
        d = p - self._last
        self._last = p

        dist = float(np.linalg.norm(d))
        if dist <= self.deadzone:
            return

        d = d * (dist - self.deadzone) / dist  # soft deadzone, no jump at the edge
        self.mouse.move_by(*(d * self.gain))

    def exit(self) -> None:
        self._last = None
