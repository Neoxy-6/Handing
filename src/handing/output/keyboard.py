from pynput.keyboard import Controller, Key, KeyCode

from handing.output.estop import EmergencyStop

ALIASES = {
    "win": "cmd",
    "pgup": "page_up",
    "pgdn": "page_down",
    "plus": "+",
    "volume_up": "media_volume_up",
    "volume_down": "media_volume_down",
    "mute": "media_volume_mute",
    "play_pause": "media_play_pause",
    "next_track": "media_next",
    "prev_track": "media_previous",
}

def parse(combo: str) -> list[Key | KeyCode]:
    """'ctrl+win+right' -> [Key.ctrl, Key.cmd, Key.right]"""
    keys = []

    for name in combo.lower().split("+"):
        name = ALIASES.get(name.strip(), name.strip())
        if len(name) == 1:
            keys.append(KeyCode.from_char(name))
        elif name in Key.__members__:
            keys.append(Key[name])
        else:
            raise ValueError(f"unknown key '{name}' in '{combo}'")

    return keys

class Keyboard:
    """every action is skipped while the emergency stop is on (in theory)"""

    def __init__(self, estop: EmergencyStop | None = None):
        self._ctl = Controller()
        self._estop = estop

    @property
    def blocked(self) -> bool:
        return self._estop is not None and self._estop.stopped

    def tap(self, combo: str) -> None:
        if self.blocked:
            return

        keys = parse(combo)
        for key in keys:
            self._ctl.press(key)
        for key in reversed(keys):
            self._ctl.release(key)

    def hold(self, combo: str) -> None:
        if not self.blocked:
            for key in parse(combo):
                self._ctl.press(key)

    def release(self, combo: str) -> None:
        """always allowed, so keys never get stuck when stop is pressed"""
        for key in reversed(parse(combo)):
            self._ctl.release(key)

    def type(self, text: str) -> None:
        if not self.blocked:
            self._ctl.type(text)
