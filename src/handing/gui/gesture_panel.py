from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QGridLayout, QHeaderView, QInputDialog, QLabel, QMessageBox, QPushButton, QTreeWidget, QTreeWidgetItem, QVBoxLayout

from handing.gui.gesture_settings import GestureSettings
from handing.gui.record_dialog import RecordDialog
from handing.gui.worker import Worker
from handing.pipeline.gesture_editor import check_name

class GesturePanel(QFrame):
    def __init__(self, worker: Worker):
        super().__init__()
        self.worker = worker
        self.names: list[str] = []

        self.setObjectName("card")

        self.list = QTreeWidget()
        self.list.setHeaderLabels(["gesture", "mode", "samples"])
        self.list.headerItem().setTextAlignment(2, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.list.setRootIsDecorated(False)
        self.list.setUniformRowHeights(True)
        header = self.list.header()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)

        buttons = QGridLayout()
        buttons.setSpacing(6)
        for text, slot, row, col, span, role in [
            ("edit gesture", self.settings, 0, 0, 2, "primary"),
            ("add", self.add, 1, 0, 1, ""),
            ("record more", self.record_more, 1, 1, 1, ""),
            ("rename", self.rename, 2, 0, 1, ""),
            ("delete", self.delete, 2, 1, 1, ""),
        ]:
            button = QPushButton(text)
            button.setProperty("role", role)
            button.clicked.connect(slot)
            buttons.addWidget(button, row, col, 1, span)

        title = QLabel("GESTURES")
        title.setProperty("role", "title")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.addWidget(title)
        layout.addWidget(self.list)
        layout.addLayout(buttons)

        self.list.itemDoubleClicked.connect(lambda *_: self.settings())
        worker.samples_changed.connect(self.show_counts)

    def show_counts(self, counts: dict[str, int]) -> None:
        self.names = list(counts)
        self.list.clear()
        gestures = self.worker.cfg.gestures

        for name, n in counts.items():
            mode = gestures[name].mode if name in gestures else "-"
            item = QTreeWidgetItem([name, mode, str(n)])
            item.setTextAlignment(2, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.list.addTopLevelItem(item)

    def selected(self) -> str | None:
        item = self.list.currentItem()
        row = self.list.indexOfTopLevelItem(item) if item else -1
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

        dialog = GestureSettings(self.worker.cfg, name, self.names, self)
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
        if not name:
            return

        text = f"delete '{name}' and all its samples?"
        if name == self.worker.cfg.safety.unlock_gesture:
            text += f"\n\n'{name}' is the unlock gesture, pick another one in app settings or control can never be unlocked."

        if QMessageBox.question(self, "delete gesture", text) == QMessageBox.StandardButton.Yes:
            self.worker.delete(name)
