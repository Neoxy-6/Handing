from handing.gamepad.mapping import PadState
from handing.output.estop import EmergencyStop

XUSB = {  # config name -> vgamepad XUSB_BUTTON member
    "A": "A", "B": "B", "X": "X", "Y": "Y",
    "LB": "LEFT_SHOULDER", "RB": "RIGHT_SHOULDER", "LS": "LEFT_THUMB", "RS": "RIGHT_THUMB",
    "BACK": "BACK", "START": "START",
    "UP": "DPAD_UP", "DOWN": "DPAD_DOWN", "LEFT": "DPAD_LEFT", "RIGHT": "DPAD_RIGHT",
}

class XboxPad:
    """virtual xbox 360 controller through vigembus, neutral while the emergency stop is on"""

    def __init__(self, estop: EmergencyStop | None = None):
        try:
            import vgamepad as vg  # only gamepad mode needs it, and it needs the vigembus driver
        except Exception as e:
            raise RuntimeError(f"gamepad mode needs vgamepad and the ViGEmBus driver: {e}") from None

        self._vg = vg
        self._estop = estop
        self._pad = vg.VX360Gamepad()
        self.state = PadState()

    @property
    def blocked(self) -> bool:
        return self._estop is not None and self._estop.stopped

    def send(self, state: PadState) -> None:
        if self.blocked:
            state = PadState()

        if state == self.state:
            return

        self.state = state
        pad, vg = self._pad, self._vg
        pad.reset()

        for name in state.pressed:
            if name in XUSB:
                pad.press_button(button = getattr(vg.XUSB_BUTTON, f"XUSB_GAMEPAD_{XUSB[name]}"))

        pad.left_trigger_float(value_float = 1.0 if "LT" in state.pressed else 0.0)
        pad.right_trigger_float(value_float = 1.0 if "RT" in state.pressed else 0.0)
        pad.left_joystick_float(*state.sticks["left"])
        pad.right_joystick_float(*state.sticks["right"])
        pad.update()

    def release(self) -> None:
        self.state = PadState()
        self._pad.reset()
        self._pad.update()

class DryPad:
    """stands in for the virtual controller, remembers the last state"""

    blocked = False

    def __init__(self):
        self.state = PadState()

    def send(self, state: PadState) -> None:
        self.state = state

    def release(self) -> None:
        self.state = PadState()

    def __str__(self) -> str:
        return describe(self.state)

def describe(state: PadState) -> str:
    (lx, ly), (rx, ry) = state.sticks["left"], state.sticks["right"]
    pressed = " ".join(sorted(state.pressed)) or "-"

    return f"L ({lx:+.2f},{ly:+.2f})  R ({rx:+.2f},{ry:+.2f})  {pressed}"
