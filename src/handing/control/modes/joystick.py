from collections.abc import Callable

import numpy as np

from handing.control.modes.base import Mode
from handing.filtering.one_euro import OneEuro

MAX_DT = 0.1  # s, a stalled frame never turns into a big jump

def joystick_speed(offset: np.ndarray, deadzone: float, curve: float) -> np.ndarray:
    """offset in radius units -> velocity in 0..1 of max speed, 0 inside the deadzone"""
    mag = float(np.linalg.norm(offset))
    if mag <= deadzone:
        return np.zeros(2)

    push = min((mag - deadzone) / (1 - deadzone), 1.0)

    return offset / mag * push ** curve

class JoystickMode(Mode):
    """distance from the stick center sets a velocity, like a gamepad stick; move gets the step each frame"""

    def __init__(self, move: Callable[[float, float], None], center: np.ndarray, radius: float, deadzone: float, max_speed: float, curve: float, smoother: OneEuro):
        self.move = move  # cursor px or wheel notches
        self.center = center  # camera px
        self.radius = radius  # camera px for full push
        self.deadzone = deadzone  # share of radius
        self.max_speed = max_speed  # units of move per second at full push
        self.curve = curve
        self.smoother = smoother
        self._last_t = 0

    def enter(self, point: np.ndarray, timestamp_ms: int) -> None:
        self.smoother.reset()
        self.smoother.update(point, timestamp_ms)
        self._last_t = timestamp_ms

    def update(self, point: np.ndarray, timestamp_ms: int) -> None:
        p = self.smoother.update(point, timestamp_ms)
        dt = min((timestamp_ms - self._last_t) / 1000, MAX_DT)
        self._last_t = timestamp_ms

        velocity = joystick_speed((p - self.center) / self.radius, self.deadzone, self.curve) * self.max_speed
        if velocity.any():
            self.move(*(velocity * dt))
