import copy

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QGridLayout, QHeaderView, QInputDialog, QLabel, QMessageBox, QPushButton, QTreeWidget, QTreeWidgetItem, QVBoxLayout

from handing.config.keys import split_key, variants
from handing.config.lint import new_warnings
from handing.config.schema import STYLED
from handing.gui.gesture_settings import GestureSettings
from handing.gui.record_dialog import RecordDialog
from handing.gui.worker import Worker
from handing.pipeline.gesture_editor import check_name

def mode_summary(gestures: dict, name: str) -> str:
    """'mouse-relative · L trigger' for a gesture with a left hand override"""
    parts = []
    for key in sorted(variants(gestures, name), key = lambda k: ("any", "left", "right").index(split_key(k)[1])):
        hand = split_key(key)[1]
        g = gestures[key]
        mode = f"{g.mode}-{g.style}" if g.mode in STYLED else g.mode
        parts.append(mode if hand == "any" else f"{hand[0].upper()} {mode}")

    return "  ·  ".join(parts) or "-"

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
        self.list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.list.setTextElideMode(Qt.TextElideMode.ElideRight)
        header = self.list.header()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)

        buttons = QGridLayout()
        buttons.setSpacing(6)
        for text, slot, row, col, span, role in [
            ("edit", self.settings, 0, 0, 2, "primary"),
            ("add", self.add, 1, 0, 1, ""),
            ("record", self.record_more, 1, 1, 1, ""),
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
            item = QTreeWidgetItem([name, mode_summary(gestures, name), str(n)])
            item.setToolTip(1, item.text(1))
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
            self.worker.configure(dialog.key(), dialog.result_gesture())

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

        cfg = self.worker.cfg
        after = copy.deepcopy(cfg)
        for key in variants(after.gestures, name):
            after.gestures.pop(key)

        warnings = new_warnings(cfg, after, self.names, [n for n in self.names if n != name])
        text = f"delete '{name}' and all its samples?"
        if warnings:
            text += "\n\n" + "\n".join(f"- {w}" for w in warnings)

        if QMessageBox.question(self, "delete gesture", text) == QMessageBox.StandardButton.Yes:
            self.worker.delete(name)
