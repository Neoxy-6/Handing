import numpy as np

from handing.control.modes.base import Mode
from handing.filtering.one_euro import OneEuro
from handing.output.mouse import Mouse

NOTCH_PX = 12  # camera px of hand movement per wheel notch at sensitivity 1

class ScrollMode(Mode):
    """hand up scrolls up, movement accumulates until a full notch"""

    def __init__(self, mouse: Mouse, sensitivity: float, smoother: OneEuro):
        self.mouse = mouse
        self.sensitivity = sensitivity
        self.smoother = smoother
        self._last = 0.0
        self._rest = 0.0

    def enter(self, point: np.ndarray, timestamp_ms: int) -> None:
        self.smoother.reset()
        self._last = float(self.smoother.update(point, timestamp_ms)[1])
        self._rest = 0.0

    def update(self, point: np.ndarray, timestamp_ms: int) -> None:
        y = float(self.smoother.update(point, timestamp_ms)[1])
        self._rest += (self._last - y) * self.sensitivity / NOTCH_PX  # image y grows downward
        self._last = y

        notches = int(self._rest)
        if notches:
            self._rest -= notches
            self.mouse.scroll(0, notches)
