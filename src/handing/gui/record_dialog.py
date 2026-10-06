from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QDialog, QLabel, QMessageBox, QProgressBar, QPushButton, QVBoxLayout

from handing.gui.worker import Worker

COUNTDOWN = 3
SAMPLES = 150  # same as each default gesture, keeps knn votes fair

class RecordDialog(QDialog):
    """countdown, then collect samples from frames with a hand"""

    def __init__(self, worker: Worker, name: str, count: int = SAMPLES, parent = None):
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
        worker.record_finished.connect(self._finished)

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

    def _finished(self, name: str, poses: list, similar) -> None:
        if name != self.name:
            return

        self._started = False

        if similar and not self._keep_anyway(similar):
            self.reject()
            return

        self.worker.add_samples(name, poses)
        self.accept()

    def _keep_anyway(self, similar) -> bool:
        text = (
            f"'{self.name}' looks like '{similar.name}'\n"
            f"{similar.ratio:.0%} of the new samples match '{similar.name}' (median distance {similar.distance:.2f})\n\n"
            "Keep anyway?"
        )
        box = QMessageBox(QMessageBox.Icon.Warning, "similar gesture", text, parent = self)
        keep = box.addButton("keep", QMessageBox.ButtonRole.AcceptRole)
        box.addButton("discard", QMessageBox.ButtonRole.RejectRole)
        box.exec()

        return box.clickedButton() is keep

    def reject(self) -> None:
        if self._started:
            self.worker.cancel_record()

        super().reject()

    def done(self, result: int) -> None:
        self.worker.record_progress.disconnect(self.bar.setValue)
        self.worker.record_finished.disconnect(self._finished)
        super().done(result)
