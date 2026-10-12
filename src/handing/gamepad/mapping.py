from dataclasses import dataclass, field

import numpy as np

from handing.config.keys import SIDES, resolve
from handing.config.schema import Config
from handing.control.modes.joystick import joystick_speed
from handing.filtering.one_euro import OneEuro
from handing.pipeline.dual import Side

@dataclass(frozen = True)
class PadState:
    sticks: dict[str, tuple[float, float]] = field(default_factory = lambda: {side: (0.0, 0.0) for side in SIDES})  # -1..1, y up
    pressed: frozenset[str] = frozenset()  # buttons and triggers held down

class Mapper:
    """each hand's palm drives the stick on its side, its gesture holds the bound button"""

    def __init__(self, cfg: Config):
        pad = cfg.gamepad
        self.pad = pad
        height = cfg.camera.width * 3 / 4  # frames are 4:3, like the cursor stick
        self.radius = pad.radius * height
        self.centers = {  # control px, x toward the user's right like Side.point
            side: np.array([x * cfg.camera.width, pad.center_y * height])
            for side, x in (("left", pad.left_center_x), ("right", pad.right_center_x))
        }
        self.smoothers = {side: OneEuro(cfg.cursor.min_cutoff, cfg.cursor.beta) for side in SIDES}

    def update(self, sides: dict[str, Side], timestamp_ms: int) -> PadState:
        sticks, pressed = {}, set()

        for side in SIDES:
            s = sides[side]
            sticks[side] = self._stick(side, s, timestamp_ms)
            if s.hand is not None:
                button = self.pad.bindings.get(resolve(self.pad.bindings, s.gesture, side))
                if button:
                    pressed.add(button)

        return PadState(sticks, frozenset(pressed))

    def _stick(self, side: str, s: Side, timestamp_ms: int) -> tuple[float, float]:
        if s.point is None or not self.pad.sticks:
            self.smoothers[side].reset()
            return 0.0, 0.0

        p = self.smoothers[side].update(s.point, timestamp_ms)
        x, y = joystick_speed((p - self.centers[side]) / self.radius, self.pad.deadzone, self.pad.curve)

        return float(x) + 0.0, 0.0 - float(y)  # image y grows downward, stick y up; + 0.0 drops -0.0
