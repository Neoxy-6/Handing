from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QDialog, QLabel, QProgressBar, QPushButton, QVBoxLayout

from handing.gui.worker import Worker

COUNTDOWN = 3

class RecordDialog(QDialog):
    """countdown, then collect samples from frames with a hand"""

    def __init__(self, worker: Worker, name: str, count: int = 60, parent = None):
        super().__init__(parent)
        self.setWindowTitle(f"record '{name}'")
        self.worker = worker
        self.name = name
        self.count = count
        self._left = COUNTDOWN
        self._started = False

        self.message = QLabel()
        self.message.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.message.setStyleSheet("font-size: 20px;")
        self.bar = QProgressBar()
        self.bar.setRange(0, count)
        cancel = QPushButton("cancel")
        cancel.clicked.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(self.message)
        layout.addWidget(QLabel("hold the gesture, move and turn your hand a little for variety"))
        layout.addWidget(self.bar)
        layout.addWidget(cancel)

        worker.record_progress.connect(self.bar.setValue)
        worker.record_done.connect(self._done)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._countdown)
        self._timer.start(1000)
        self._show_left()

    def _show_left(self) -> None:
        self.message.setText(f"get ready... {self._left}")

    def _countdown(self) -> None:
        self._left -= 1
        if self._left > 0:
            self._show_left()
            return

        self._timer.stop()
        self._started = True
        self.message.setText("recording")
        self.worker.record(self.name, self.count)

    def _done(self, name: str) -> None:
        if name == self.name:
            self.accept()

    def reject(self) -> None:
        if self._started:
            self.worker.cancel_record()

        super().reject()

    def done(self, result: int) -> None:
        self.worker.record_progress.disconnect(self.bar.setValue)
        self.worker.record_done.disconnect(self._done)
        super().done(result)
