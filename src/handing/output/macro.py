import threading
import time
from dataclasses import dataclass

from handing.output import keyboard
from handing.output.keyboard import Keyboard
from handing.output.mouse import BUTTONS, Mouse

MACRO_PREFIX = "macro:"

@dataclass(frozen = True)
class Step:
    kind: str  # tap, hold, release, type, wait, click, scroll
    value: str | int

def parse_step(raw: dict) -> Step:
    if not isinstance(raw, dict) or len(raw) != 1:
        raise ValueError(f"macro step must have exactly one key: {raw}")

    kind, value = next(iter(raw.items()))

    if kind in ("tap", "hold", "release"):
        keyboard.parse(str(value))
    elif kind == "click" and value not in BUTTONS:
        raise ValueError(f"unknown mouse button '{value}'")
    elif kind in ("wait", "scroll") and not isinstance(value, int):
        raise ValueError(f"'{kind}' needs an integer, got {value!r}")
    elif kind not in ("type", "click", "wait", "scroll"):
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
        held: list[str] = []

        try:
            for step in steps:
                if self._kb.blocked:
                    break

                if step.kind == "tap":
                    self._kb.tap(step.value)
                elif step.kind == "hold":
                    self._kb.hold(step.value)
                    held.append(step.value)
                elif step.kind == "release":
                    self._kb.release(step.value)
                    held = [h for h in held if h != step.value]
                elif step.kind == "type":
                    self._kb.type(str(step.value))
                elif step.kind == "click":
                    self._mouse.click(step.value)
                elif step.kind == "scroll":
                    self._mouse.scroll(0, step.value)
                elif step.kind == "wait":
                    self._wait(step.value)
        finally:
            for combo in reversed(held):
                self._kb.release(combo)

            self._busy.release()

    def _wait(self, ms: int) -> None:
        """sleep in small slices so the emergency stop interrupts it"""
        end = time.perf_counter() + ms / 1000

        while time.perf_counter() < end and not self._kb.blocked:
            time.sleep(0.01)
