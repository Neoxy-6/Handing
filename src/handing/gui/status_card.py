import time

from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout

from handing.control.states import State
from handing.gui.style import STATE_COLORS

class StatusCard(QFrame):
    """state dot and name, the running gesture in large type, raw prediction and fps underneath"""

    def __init__(self):
        super().__init__()
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

        pred = tick.prediction
        self.raw.setText(f"{pred.name}  ·  {pred.confidence:.0%}  ·  {pred.distance:.2f}" if pred else "no hand")

        now = time.perf_counter()
        self.fps.setText(f"{1 / max(now - self._last_tick, 1e-6):.0f} fps")
        self._last_tick = now
