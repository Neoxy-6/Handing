import math

import numpy as np

def _alpha(cutoff: float, dt: float) -> float:
    tau = 1 / (2 * math.pi * cutoff)

    return 1 / (1 + tau / dt)

class OneEuro:
    """low cutoff when slow (less jitter), higher when fast (less lag)"""

    # defaults tuned by scripts/bench_cursor.py on pixel coords of a 640 px wide frame
    def __init__(self, min_cutoff: float = 0.5, beta: float = 0.02, d_cutoff: float = 1.0):
        self.min_cutoff = min_cutoff
        self.beta = beta
        self.d_cutoff = d_cutoff
        self.reset()

    def reset(self) -> None:
        self._x = None
        self._dx = None
        self._t = 0

    def update(self, x: np.ndarray, timestamp_ms: int) -> np.ndarray:
        x = np.asarray(x, np.float64)
        if self._x is None:
            self._x, self._dx, self._t = x, np.zeros_like(x), timestamp_ms
            return x

        dt = max((timestamp_ms - self._t) / 1000, 1e-3)
        self._t = timestamp_ms

        a_d = _alpha(self.d_cutoff, dt)
        self._dx = a_d * (x - self._x) / dt + (1 - a_d) * self._dx

        cutoff = self.min_cutoff + self.beta * float(np.linalg.norm(self._dx))
        a = _alpha(cutoff, dt)
        self._x = a * x + (1 - a) * self._x

        return self._x
