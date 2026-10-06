from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QColor, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

from handing.control.states import State
from handing.gui.worker import Worker

COLORS = {
    State.STANDBY: "#777777",
    State.LOCKED: "#777777",
    State.IDLE: "#3b82f6",
    State.ACTIVE: "#22c55e",
}
LIVE_DOT = "#ef4444"

def make_icon(state: State, live: bool) -> QIcon:
    """state colored circle, red dot in the corner while output is live"""
    pixmap = QPixmap(64, 64)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor(COLORS[state]))
    painter.drawEllipse(4, 4, 56, 56)

    if live:
        painter.setBrush(QColor(LIVE_DOT))
        painter.drawEllipse(36, 36, 26, 26)

    painter.end()

    return QIcon(pixmap)

class Tray(QSystemTrayIcon):
    def __init__(self, window, worker: Worker):
        super().__init__()
        self.window = window
        self.worker = worker
        self._state = State.STANDBY
        self._live = False
        self._hint_shown = False

        menu = QMenu()
        menu.addAction("show", self.show_window)
        self.output = QAction("output", menu, checkable = True)
        self.output.toggled.connect(worker.set_output)
        menu.addAction(self.output)
        menu.addSeparator()
        menu.addAction("quit", self.quit)
        self.setContextMenu(menu)

        self.activated.connect(self._on_activated)
        window.visibility_changed.connect(self._on_window_visible)
        worker.tick.connect(lambda tick: self._update(tick.status.state, self._live))
        worker.output_changed.connect(lambda live: self._update(self._state, live))
        self._update(self._state, self._live, force = True)

    def _update(self, state: State, live: bool, force: bool = False) -> None:
        """repaint only when something changed, ticks arrive every frame"""
        if not force and (state, live) == (self._state, self._live):
            return

        self._state, self._live = state, live
        self.setIcon(make_icon(state, live))
        self.setToolTip(f"Handing - {state.value}, output {'on' if live else 'off'}")

        self.output.blockSignals(True)
        self.output.setChecked(live)
        self.output.blockSignals(False)

    def _on_window_visible(self, visible: bool) -> None:
        """tell where the app went the first time it hides, windows 11 tucks new icons under ^"""
        if visible or self._hint_shown or self.window.quitting:
            return

        self._hint_shown = True
        self.showMessage(
            "Handing is still running",
            "Click the Handing icon in the tray (under ^ on the taskbar) to open it again.",
            self.icon(),
            5000,
        )

    def _on_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.show_window()

    def show_window(self) -> None:
        self.window.showNormal()
        self.window.raise_()
        self.window.activateWindow()

    def quit(self) -> None:
        self.window.quitting = True
        self.worker.stop()
        self.hide()
        QApplication.quit()
