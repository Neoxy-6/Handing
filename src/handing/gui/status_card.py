import time

from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout

from handing.config.schema import Config
from handing.control.states import State
from handing.gamepad.runner import GamepadTick
from handing.gui.style import STATE_COLORS

def pad_text(tick: GamepadTick, swap: bool) -> str:
    """'L fist (+0.4,-0.1)  ·  R -' per hand, the values of the stick that hand drives"""
    parts = []
    for side, s in tick.sides.items():
        stick = ("right" if side == "left" else "left") if swap else side
        x, y = tick.pad.sticks[stick]
        parts.append(f"{side[0].upper()} {s.gesture} ({x:+.1f},{y:+.1f})" if s.hand else f"{side[0].upper()} -")

    return "  ·  ".join(parts)

class StatusCard(QFrame):
    """state dot and name, the running gesture in large type, raw prediction and fps underneath"""

    def __init__(self, cfg: Config):
        super().__init__()
        self.cfg = cfg  # the worker's, so a stick swap shows up without rebuilding the card
        self.setObjectName("card")

        self.dot = QLabel()
        self.dot.setFixedSize(10, 10)
        self.state = QLabel()
        self.state.setStyleSheet("font-size: 14px; font-weight: 600;")
        self.gesture = QLabel("-")
        self.gesture.setStyleSheet("font-size: 26px; font-weight: 700;")
        self.raw = QLabel("no hand")
        self.raw.setProperty("role", "muted")
        self.fps = QLabel("- fps")
        self.fps.setProperty("role", "muted")
        self._last_tick = time.perf_counter()

        title = QHBoxLayout()
        title.addWidget(self.dot)
        title.addWidget(self.state)
        title.addStretch()
        title.addWidget(self.fps)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.addLayout(title)
        layout.addWidget(self.gesture)
        layout.addWidget(self.raw)

        self._state = None
        self.set_state(State.STANDBY)

    def set_state(self, state: State) -> None:
        if state == self._state:
            return

        self._state = state
        self.state.setText(state.value)
        self.dot.setStyleSheet(f"background: {STATE_COLORS[state]}; border-radius: 5px;")

    def update_tick(self, tick) -> None:
        self.set_state(tick.status.state)
        self.gesture.setText(tick.status.gesture or "-")

        if isinstance(tick, GamepadTick):
            self.raw.setText(pad_text(tick, self.cfg.gamepad.swap))
        else:
            pred = tick.prediction
            self.raw.setText(f"{pred.name}  ·  {pred.confidence:.0%}  ·  {pred.distance:.2f}" if pred else "no hand")

        now = time.perf_counter()
        self.fps.setText(f"{1 / max(now - self._last_tick, 1e-6):.0f} fps")
        self._last_tick = now
