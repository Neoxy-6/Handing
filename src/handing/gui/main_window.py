import time

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFormLayout, QHBoxLayout, QLabel, QMainWindow, QMessageBox, QPushButton, QVBoxLayout, QWidget

from handing.gui.frame_view import FrameView
from handing.gui.gesture_panel import GesturePanel
from handing.gui.render import draw_hands
from handing.gui.worker import Worker

def pretty_hotkey(hotkey: str) -> str:
    """'<ctrl>+<alt>+q' -> 'Ctrl+Alt+Q'"""
    return "+".join(k.strip("<>").capitalize() for k in hotkey.split("+"))

class MainWindow(QMainWindow):
    visibility_changed = Signal(bool)

    def __init__(self, worker: Worker):
        super().__init__()
        self.setWindowTitle("Handing")
        self.resize(960, 540)

        self.worker = worker
        self.quitting = False  # set before QApplication.quit so close really closes
        self.view = FrameView()
        self.state = QLabel("-")
        self.gesture = QLabel("-")
        self.raw = QLabel("-")
        self.fps = QLabel("-")
        self.output = QPushButton()
        self.output.setCheckable(True)
        self._last_tick = time.perf_counter()

        info = QFormLayout()
        info.addRow("state", self.state)
        info.addRow("gesture", self.gesture)
        info.addRow("raw", self.raw)
        info.addRow("fps", self.fps)

        side = QVBoxLayout()
        side.addLayout(info)
        side.addWidget(QLabel("gestures"))
        side.addWidget(GesturePanel(worker))
        side.addWidget(QLabel(f"{pretty_hotkey(worker.cfg.safety.estop_hotkey)} toggles output"))
        side.addWidget(self.output)

        root = QHBoxLayout()
        root.addWidget(self.view, 3)
        root.addLayout(side, 1)

        central = QWidget()
        central.setLayout(root)
        self.setCentralWidget(central)

        self.output.toggled.connect(worker.set_output)
        worker.output_changed.connect(self.on_output_changed)
        worker.tick.connect(self.on_tick)
        worker.failed.connect(self.on_failed)
        self.on_output_changed(False)

    def on_tick(self, tick) -> None:
        if not self.isVisible():
            return

        self.view.show_frame(draw_hands(tick.frame.copy(), tick.hands))

        self.state.setText(tick.status.state.value)
        self.gesture.setText(tick.status.gesture or "-")
        pred = tick.prediction
        self.raw.setText(f"{pred.name}  {pred.confidence:.2f}  d {pred.distance:.2f}" if pred else "no hand")

        now = time.perf_counter()
        self.fps.setText(f"{1 / max(now - self._last_tick, 1e-6):.0f}")
        self._last_tick = now

    def on_output_changed(self, live: bool) -> None:
        self.output.blockSignals(True)
        self.output.setChecked(live)
        self.output.blockSignals(False)

        self.output.setText("output ON" if live else "output OFF")
        self.output.setStyleSheet("background: #c33; color: white;" if live else "")

    def on_failed(self, message: str) -> None:
        QMessageBox.critical(self, "Handing", message)

    def showEvent(self, event) -> None:
        self.visibility_changed.emit(True)
        super().showEvent(event)

    def hideEvent(self, event) -> None:
        if not self.quitting:
            self.visibility_changed.emit(False)
        super().hideEvent(event)

    def closeEvent(self, event) -> None:
        """hide to tray, quit from the tray menu"""
        if self.quitting:
            super().closeEvent(event)
            return

        event.ignore()
        self.hide()
