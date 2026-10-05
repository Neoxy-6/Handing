import numpy as np

from handing.control.modes.base import Mode
from handing.output.macro import ActionRunner

class ActionMode(Mode):
    """runs the action when the gesture appears, optionally again every repeat_ms while held"""

    def __init__(self, runner: ActionRunner, action: str, repeat: bool):
        self.runner = runner
        self.action = action
        self.repeat = repeat

    def enter(self, point: np.ndarray, timestamp_ms: int) -> None:
        self.runner.run_repeat(self.action, timestamp_ms)

    def update(self, point: np.ndarray, timestamp_ms: int) -> None:
        if self.repeat:
            self.runner.run_repeat(self.action, timestamp_ms)
