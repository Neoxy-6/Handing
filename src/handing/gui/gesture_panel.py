from PySide6.QtWidgets import QGridLayout, QInputDialog, QListWidget, QMessageBox, QPushButton, QVBoxLayout, QWidget

from handing.gui.gesture_settings import GestureSettings
from handing.gui.record_dialog import RecordDialog
from handing.gui.worker import Worker
from handing.pipeline.gesture_editor import check_name

class GesturePanel(QWidget):
    def __init__(self, worker: Worker):
        super().__init__()
        self.worker = worker
        self.names: list[str] = []

        self.list = QListWidget()
        buttons = QGridLayout()
        for text, slot, row, col, span in [
            ("edit gesture", self.settings, 0, 0, 2),
            ("add", self.add, 1, 0, 1),
            ("record more", self.record_more, 1, 1, 1),
            ("rename", self.rename, 2, 0, 1),
            ("delete", self.delete, 2, 1, 1),
        ]:
            button = QPushButton(text)
            button.clicked.connect(slot)
            buttons.addWidget(button, row, col, 1, span)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.list)
        layout.addLayout(buttons)

        self.list.itemDoubleClicked.connect(self.settings)
        worker.samples_changed.connect(self.show_counts)

    def show_counts(self, counts: dict[str, int]) -> None:
        self.names = list(counts)
        self.list.clear()
        gestures = self.worker.cfg.gestures

        for name, n in counts.items():
            mode = gestures[name].mode if name in gestures else "-"
            self.list.addItem(f"{name}  [{mode}]  ({n} samples)")

    def selected(self) -> str | None:
        row = self.list.currentRow()
        return self.names[row] if 0 <= row < len(self.names) else None

    def ask_name(self, title: str, text: str = "") -> str | None:
        name, ok = QInputDialog.getText(self, title, "gesture name", text = text)
        if not ok:
            return None

        name = name.strip()
        error = check_name(name, self.names)
        if error:
            QMessageBox.warning(self, title, error)
            return None

        return name

    def settings(self) -> None:
        name = self.selected()
        if not name:
            return

        dialog = GestureSettings(self.worker.cfg, name, self)
        if dialog.exec():
            self.worker.configure(name, dialog.result_gesture())

    def add(self) -> None:
        name = self.ask_name("add gesture")
        if name:
            RecordDialog(self.worker, name, parent = self).exec()

    def record_more(self) -> None:
        name = self.selected()
        if name:
            RecordDialog(self.worker, name, parent = self).exec()

    def rename(self) -> None:
        old = self.selected()
        new = old and self.ask_name("rename gesture", old)
        if new:
            self.worker.rename(old, new)

    def delete(self) -> None:
        name = self.selected()
        if name and QMessageBox.question(self, "delete gesture", f"delete '{name}' and all its samples?") == QMessageBox.StandardButton.Yes:
            self.worker.delete(name)
