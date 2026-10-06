from PySide6.QtCore import QPropertyAnimation, QRectF, Qt, QTimer
from PySide6.QtGui import QColor, QFont, QFontMetrics, QGuiApplication, QPainter
from PySide6.QtWidgets import QWidget

from handing.control.states import State
from handing.gui.style import STATE_COLORS as COLORS
from handing.gui.worker import Worker

MARGIN = 16
BRIGHT, DIM = 0.95, 0.35
DIM_AFTER_MS = 2000

class Overlay(QWidget):
    """small always-on-top pill, click-through, shown only while the main window is hidden"""

    def __init__(self, worker: Worker):
        super().__init__(None, Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool | Qt.WindowType.WindowTransparentForInput)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)

        self.font_ = QFont(self.font().family(), 11, QFont.Weight.Bold)
        self.enabled = False
        self._state = State.STANDBY
        self._gesture: str | None = None
        self._live = False

        self._fade = QPropertyAnimation(self, b"windowOpacity", self)
        self._fade.setDuration(400)
        self._dim = QTimer(self, singleShot = True, interval = DIM_AFTER_MS)
        self._dim.timeout.connect(lambda: self._fade_to(DIM))

        worker.tick.connect(lambda tick: self._update(tick.status.state, tick.status.gesture, self._live))
        worker.output_changed.connect(lambda live: self._update(self._state, self._gesture, live))

    def set_enabled(self, enabled: bool) -> None:
        self.enabled = enabled
        if enabled:
            self._relayout()
            self.show()
            self._flash()
        else:
            self.hide()

    def text(self) -> str:
        label = {State.STANDBY: "no hand", State.LOCKED: "locked", State.IDLE: "idle"}.get(self._state, self._gesture or "")
        return label if self._live else f"{label} · off"

    def _update(self, state: State, gesture: str | None, live: bool) -> None:
        if (state, gesture, live) == (self._state, self._gesture, self._live):
            return

        self._state, self._gesture, self._live = state, gesture, live
        if self.enabled:
            self._relayout()
            self.update()
            self._flash()

    def _relayout(self) -> None:
        """size to the text, bottom right of the primary screen above the taskbar"""
        metrics = QFontMetrics(self.font_)
        h = metrics.height() + 14
        w = metrics.horizontalAdvance(self.text()) + int(h * 0.4) + 44  # text + dot + padding
        area = QGuiApplication.primaryScreen().availableGeometry()
        self.setGeometry(area.right() - w - MARGIN, area.bottom() - h - MARGIN, w, h)

    def _flash(self) -> None:
        self._fade_to(BRIGHT)
        self._dim.start()

    def _fade_to(self, opacity: float) -> None:
        self._fade.stop()
        self._fade.setStartValue(self.windowOpacity())
        self._fade.setEndValue(opacity)
        self._fade.start()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = QRectF(self.rect())

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(30, 30, 30, 220))
        painter.drawRoundedRect(rect, rect.height() / 2, rect.height() / 2)

        dot = rect.height() * 0.4
        painter.setBrush(QColor(COLORS[self._state]))
        painter.drawEllipse(QRectF(12, (rect.height() - dot) / 2, dot, dot))

        painter.setPen(QColor("white"))
        painter.setFont(self.font_)
        painter.drawText(rect.adjusted(16 + dot, 0, -12, 0), Qt.AlignmentFlag.AlignVCenter, self.text())
