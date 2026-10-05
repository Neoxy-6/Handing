from pynput.mouse import Button, Controller

from handing.output.estop import EmergencyStop

BUTTONS = {"left": Button.left, "right": Button.right, "middle": Button.middle}

class Mouse:
    """every action is skipped while the emergency stop is on"""

    def __init__(self, estop: EmergencyStop | None = None):
        self._ctl = Controller()
        self._estop = estop
        self._rest = [0.0, 0.0]  # sub-pixel remainder of relative moves

    @property
    def blocked(self) -> bool:
        return self._estop is not None and self._estop.stopped

    @property
    def position(self) -> tuple[int, int]:
        return self._ctl.position

    def move_by(self, dx: float, dy: float) -> None:
        if self.blocked:
            return

        x, y = self._rest[0] + dx, self._rest[1] + dy
        ix, iy = int(x), int(y)
        self._rest = [x - ix, y - iy]

        if ix or iy:
            self._ctl.move(ix, iy)

    def move_to(self, x: float, y: float) -> None:
        if not self.blocked:
            self._ctl.position = (round(x), round(y))

    def click(self, button: str = "left", count: int = 1) -> None:
        if not self.blocked:
            self._ctl.click(BUTTONS[button], count)

    def press(self, button: str = "left") -> None:
        if not self.blocked:
            self._ctl.press(BUTTONS[button])

    def release(self, button: str = "left") -> None:
        """always allowed, so a drag never gets stuck when stop is pressed"""
        self._ctl.release(BUTTONS[button])

    def scroll(self, dx: int, dy: int) -> None:
        if not self.blocked:
            self._ctl.scroll(dx, dy)
