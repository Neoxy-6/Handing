from handing.gamepad.mapping import PadState

class DryPad:
    """stands in for the virtual controller, remembers the last state"""

    def __init__(self):
        self.state = PadState()

    def send(self, state: PadState) -> None:
        self.state = state

    def release(self) -> None:
        self.state = PadState()

    def __str__(self) -> str:
        (lx, ly), (rx, ry) = self.state.sticks["left"], self.state.sticks["right"]
        pressed = " ".join(sorted(self.state.pressed)) or "-"

        return f"L ({lx:+.2f},{ly:+.2f})  R ({rx:+.2f},{ry:+.2f})  {pressed}"
