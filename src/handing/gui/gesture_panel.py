from PySide6.QtWidgets import QGridLayout, QInputDialog, QListWidget, QMessageBox, QPushButton, QVBoxLayout, QWidget

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
        for i, (text, slot) in enumerate([
            ("add", self.add),
            ("record more", self.record_more),
            ("rename", self.rename),
            ("delete", self.delete),
        ]):
            button = QPushButton(text)
            button.clicked.connect(slot)
            buttons.addWidget(button, i // 2, i % 2)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.list)
        layout.addLayout(buttons)

        worker.samples_changed.connect(self.show_counts)

    def show_counts(self, counts: dict[str, int]) -> None:
        self.names = list(counts)
        self.list.clear()
        self.list.addItems([f"{name}  ({n} samples)" for name, n in counts.items()])

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
