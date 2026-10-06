import time

class Throttle:
    """slows the loop down while no hand is seen, full speed again as soon as one shows up"""

    def __init__(self, idle_fps: int = 8, grace_ms: int = 1000):
        self.idle_fps = idle_fps  # 0 disables
        self.grace_ms = grace_ms  # stay at full speed this long after the hand leaves
        self._last_hand = 0.0
        self._last_frame = 0.0

    def wait(self) -> None:
        """call before reading a frame"""
        now = time.perf_counter()
        idle = (now - self._last_hand) * 1000 > self.grace_ms

        if self.idle_fps > 0 and idle:
            delay = self._last_frame + 1 / self.idle_fps - now
            if delay > 0:
                time.sleep(delay)

        self._last_frame = time.perf_counter()

    def saw_hand(self) -> None:
        self._last_hand = time.perf_counter()
