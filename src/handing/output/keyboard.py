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

    def __init__(self, estop: EmergencyStop | None = None, repeat_ms: int = 300):
        self._ctl = Controller()
        self._estop = estop
        self.repeat_ms = repeat_ms
        self._last: dict[str, int] = {}

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

    def tap_repeat(self, combo: str, timestamp_ms: int) -> bool:
        """tap at most once per repeat_ms, for held gestures; return True if tapped"""
        if timestamp_ms - self._last.get(combo, -self.repeat_ms) < self.repeat_ms:
            return False

        self._last[combo] = timestamp_ms
        self.tap(combo)

        return True
