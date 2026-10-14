from dataclasses import dataclass, field

import numpy as np

from handing.config.keys import SIDES, resolve
from handing.config.schema import Config, PadBinding
from handing.control.modes.joystick import joystick_speed
from handing.filtering.one_euro import OneEuro
from handing.pipeline.dual import Side

@dataclass(frozen = True)
class PadState:
    sticks: dict[str, tuple[float, float]] = field(default_factory = lambda: {side: (0.0, 0.0) for side in SIDES})  # -1..1, y up
    pressed: frozenset[str] = frozenset()  # buttons and triggers held down
    driving: frozenset[str] = frozenset()  # hands whose palm drives a stick right now

class Mapper:
    """each hand's palm drives a stick (its own side unless swapped), its gesture holds the bound button"""

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
        self.repeat_ms = cfg.keyboard.repeat_ms  # one press and release per period, like repeated actions
        self._held: dict[str, tuple[str, int]] = {}  # side -> (binding key, when it started)

    def update(self, sides: dict[str, Side], timestamp_ms: int) -> PadState:
        sticks, pressed, driving = {}, set(), set()

        for side in SIDES:
            s = sides[side]
            binding = self._binding(side, s, timestamp_ms)

            if self._drives(s, binding):
                driving.add(side)
                sticks[self.stick_of(side)] = self._stick(side, s, timestamp_ms)
            else:
                self.smoothers[side].reset()
                sticks[self.stick_of(side)] = (0.0, 0.0)

            button = self._button(side, binding, timestamp_ms)
            if button:
                pressed.add(button)

        return PadState(sticks, frozenset(pressed), frozenset(driving))

    def stick_of(self, side: str) -> str:
        """which stick this hand drives"""
        return ("right" if side == "left" else "left") if self.pad.swap else side

    def _binding(self, side: str, s: Side, timestamp_ms: int) -> PadBinding | None:
        """what this hand's gesture is bound to, remembers when it started for repeating buttons"""
        key = resolve(self.pad.bindings, s.gesture, side) if s.hand is not None else None
        binding = self.pad.bindings.get(key) if key else None
        if binding is None:
            self._held.pop(side, None)
        elif self._held.get(side, (None,))[0] != key:
            self._held[side] = (key, timestamp_ms)

        return binding

    def _drives(self, s: Side, binding: PadBinding | None) -> bool:
        if s.point is None or self.pad.sticks == "off":
            return False

        return self.pad.sticks == "always" or bool(binding and binding.stick)

    def _button(self, side: str, binding: PadBinding | None, timestamp_ms: int) -> str | None:
        """the bound button while the gesture is held, a repeating one only in the first half of each period"""
        if binding is None or binding.button is None:
            return None

        if not binding.repeat:
            return binding.button

        elapsed = timestamp_ms - self._held[side][1]

        return binding.button if elapsed % self.repeat_ms < self.repeat_ms / 2 else None

    def _stick(self, side: str, s: Side, timestamp_ms: int) -> tuple[float, float]:
        p = self.smoothers[side].update(s.point, timestamp_ms)
        x, y = joystick_speed((p - self.centers[side]) / self.radius, self.pad.deadzone, self.pad.curve)

        return float(x) + 0.0, 0.0 - float(y)  # image y grows downward, stick y up; + 0.0 drops -0.0
