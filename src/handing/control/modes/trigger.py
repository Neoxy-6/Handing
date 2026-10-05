import numpy as np

from handing.control.modes.base import Mode
from handing.output.macro import ActionRunner

REARM = 0.4  # back within this fraction of the threshold to fire again

class TriggerMode(Mode):
    """fires once when the hand moves past the threshold from where the gesture started"""

    def __init__(self, runner: ActionRunner, actions: dict[str, str | None], threshold_px: float):
        self.runner = runner
        self.actions = actions  # left/right/up/down -> action
        self.threshold_px = threshold_px
        self._origin: np.ndarray | None = None
        self._armed = False

    def enter(self, point: np.ndarray, timestamp_ms: int) -> None:
        self._origin = point.copy()
        self._armed = True

    def update(self, point: np.ndarray, timestamp_ms: int) -> None:
        dx, dy = point - self._origin
        dist = max(abs(dx), abs(dy))

        if not self._armed:
            self._armed = dist < self.threshold_px * REARM
            return

        if dist < self.threshold_px:
            return

        if abs(dx) >= abs(dy):
            direction = "right" if dx > 0 else "left"
        else:
            direction = "down" if dy > 0 else "up"

        action = self.actions.get(direction)
        if action:
            self.runner.run(action)

        self._armed = False

    def exit(self) -> None:
        self._origin = None
