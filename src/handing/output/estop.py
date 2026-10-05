import threading
from collections.abc import Callable

from pynput import keyboard

DEFAULT_HOTKEY = "<ctrl>+<alt>+q"

class EmergencyStop:
    """global hotkey toggles a stop flag, output modules check it before acting (not for FRC xd)"""

    def __init__(self, hotkey: str = DEFAULT_HOTKEY, on_change: Callable[[bool], None] | None = None):
        self._stopped = threading.Event()
        self._on_change = on_change
        self._listener = keyboard.GlobalHotKeys({hotkey: self.toggle})

    @property
    def stopped(self) -> bool:
        return self._stopped.is_set()

    def toggle(self) -> None:
        if self.stopped:
            self._stopped.clear()
        else:
            self._stopped.set()

        if self._on_change:
            self._on_change(self.stopped)

    def start(self) -> None:
        self._listener.start()

    def close(self) -> None:
        self._listener.stop()

    def __enter__(self) -> "EmergencyStop":
        self.start()
        return self

    def __exit__(self, *_) -> None:
        self.close()
