import threading
import time
from dataclasses import dataclass

from handing.output import keyboard
from handing.output.keyboard import Keyboard
from handing.output.mouse import BUTTONS, Mouse

MACRO_PREFIX = "macro:"

KEY_STEPS = ("tap", "hold", "release")
BUTTON_STEPS = ("click", "double_click", "mouse_down", "mouse_up")
POINT_STEPS = ("move", "move_to")

@dataclass(frozen = True)
class Step:
    kind: str
    value: str | int | tuple[int, int]

def _point(kind: str, value) -> tuple[int, int]:
    if not (isinstance(value, list) and len(value) == 2 and all(isinstance(v, int) for v in value)):
        raise ValueError(f"'{kind}' needs [x, y] integers, got {value!r}")

    return value[0], value[1]

def parse_step(raw: dict) -> Step:
    if not isinstance(raw, dict) or len(raw) != 1:
        raise ValueError(f"macro step must have exactly one key: {raw}")

    kind, value = next(iter(raw.items()))

    if kind in KEY_STEPS:
        keyboard.parse(str(value))
    elif kind in BUTTON_STEPS:
        if value not in BUTTONS:
            raise ValueError(f"unknown mouse button '{value}'")
    elif kind in POINT_STEPS:
        value = _point(kind, value)
    elif kind == "scroll":
        value = (0, value) if isinstance(value, int) else _point(kind, value)
    elif kind == "wait":
        if not isinstance(value, int):
            raise ValueError(f"'wait' needs an integer, got {value!r}")
    elif kind == "type":
        value = str(value)
    else:
        raise ValueError(f"unknown macro step '{kind}'")

    return Step(kind, value)

def parse_macro(raw: list) -> list[Step]:
    return [parse_step(step) for step in raw]

def check_action(action: str, macros: dict[str, list[Step]]) -> None:
    """raise ValueError if the action cannot run"""
    if action.startswith(MACRO_PREFIX):
        if action[len(MACRO_PREFIX):] not in macros:
            raise ValueError(f"unknown macro in '{action}'")
    else:
        keyboard.parse(action)

class ActionRunner:
    """runs key combos directly and macros on a background thread, one macro at a time"""

    def __init__(self, kb: Keyboard, mouse: Mouse, macros: dict[str, list[Step]], repeat_ms: int = 300):
        self._kb = kb
        self._mouse = mouse
        self.macros = macros
        self.repeat_ms = repeat_ms
        self._last: dict[str, int] = {}
        self._busy = threading.Lock()

    def run(self, action: str) -> bool:
        """return False if skipped because another macro is still running"""
        if not action.startswith(MACRO_PREFIX):
            self._kb.tap(action)
            return True

        if not self._busy.acquire(blocking = False):
            return False

        steps = self.macros[action[len(MACRO_PREFIX):]]
        threading.Thread(target = self._execute, args = (steps,), daemon = True).start()

        return True

    def run_repeat(self, action: str, timestamp_ms: int) -> bool:
        """run at most once per repeat_ms, for held gestures"""
        if timestamp_ms - self._last.get(action, -self.repeat_ms) < self.repeat_ms:
            return False

        self._last[action] = timestamp_ms

        return self.run(action)

    def _execute(self, steps: list[Step]) -> None:
        keys: list[str] = []
        buttons: list[str] = []

        try:
            for step in steps:
                if self._kb.blocked:
                    break

                self._do(step, keys, buttons)
        finally:
            for combo in reversed(keys):
                self._kb.release(combo)
            for button in buttons:
                self._mouse.release(button)

            self._busy.release()

    def _do(self, step: Step, keys: list[str], buttons: list[str]) -> None:
        kind, value = step.kind, step.value

        if kind == "tap":
            self._kb.tap(value)
        elif kind == "hold":
            self._kb.hold(value)
            keys.append(value)
        elif kind == "release":
            self._kb.release(value)
            keys[:] = [k for k in keys if k != value]
        elif kind == "type":
            self._kb.type(value)
        elif kind == "click":
            self._mouse.click(value)
        elif kind == "double_click":
            self._mouse.click(value, 2)
        elif kind == "mouse_down":
            self._mouse.press(value)
            buttons.append(value)
        elif kind == "mouse_up":
            self._mouse.release(value)
            buttons[:] = [b for b in buttons if b != value]
        elif kind == "move":
            self._mouse.move_by(*value)
        elif kind == "move_to":
            self._mouse.move_to(*value)
        elif kind == "scroll":
            self._mouse.scroll(*value)
        elif kind == "wait":
            self._wait(value)

    def _wait(self, ms: int) -> None:
        """sleep in small slices so the emergency stop interrupts it"""
        end = time.perf_counter() + ms / 1000

        while time.perf_counter() < end and not self._kb.blocked:
            time.sleep(0.01)
