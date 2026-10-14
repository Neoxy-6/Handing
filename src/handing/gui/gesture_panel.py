import copy

from PySide6.QtCore import QModelIndex, Qt, Signal
from PySide6.QtWidgets import QFrame, QGridLayout, QHeaderView, QInputDialog, QLabel, QMessageBox, QPushButton, QTreeWidget, QTreeWidgetItem, QVBoxLayout

from handing.config.keys import SIDES, resolve, split_key, variants
from handing.config.lint import new_warnings
from handing.config.schema import STYLED
from handing.gui.gesture_settings import GestureSettings
from handing.gui.pad_binding_dialog import PadBindingDialog
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

def binding_text(bindings: dict, name: str, side: str) -> str:
    """'RT', 'A ↻' when it repeats, '-' when that hand presses nothing"""
    binding = bindings.get(resolve(bindings, name, side))
    if binding is None:
        return "-"

    return f"{binding.button} ↻" if binding.repeat else binding.button

class GestureList(QTreeWidget):
    """flat list the user can reorder by dragging"""

    reordered = Signal(list)

    def __init__(self):
        super().__init__()
        self.setDragDropMode(QTreeWidget.DragDropMode.InternalMove)
        self.setDefaultDropAction(Qt.DropAction.MoveAction)

    def names(self) -> list[str]:
        return [self.topLevelItem(i).text(0) for i in range(self.topLevelItemCount())]

    def dropEvent(self, event) -> None:
        super().dropEvent(event)
        self.reordered.emit(self.names())

    def mousePressEvent(self, event) -> None:
        """a click on empty space clears the selection"""
        if self.itemAt(event.position().toPoint()) is None:
            self.clearSelection()
            self.setCurrentIndex(QModelIndex())

        super().mousePressEvent(event)

class GesturePanel(QFrame):
    def __init__(self, worker: Worker):
        super().__init__()
        self.worker = worker
        self.names: list[str] = []

        self.setObjectName("card")

        self.list = GestureList()
        self.list.reordered.connect(self._reordered)
        self.list.setRootIsDecorated(False)
        self.list.setUniformRowHeights(True)
        self.list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.list.setTextElideMode(Qt.TextElideMode.ElideRight)
        self.list.header().setStretchLastSection(False)

        buttons = QGridLayout()
        buttons.setSpacing(6)
        self.needs_selection: list[QPushButton] = []
        for text, slot, row, col, span, role, per_gesture in [
            ("add", self.add, 0, 0, 2, "primary", False),
            ("edit", self.settings, 1, 0, 1, "", True),
            ("record", self.record_more, 1, 1, 1, "", True),
            ("rename", self.rename, 2, 0, 1, "", True),
            ("delete", self.delete, 2, 1, 1, "", True),
        ]:
            button = QPushButton(text)
            button.setProperty("role", role)
            button.clicked.connect(slot)
            buttons.addWidget(button, row, col, 1, span)
            if per_gesture:
                self.needs_selection.append(button)

        title = QLabel("GESTURES")
        title.setProperty("role", "title")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.addWidget(title)
        layout.addWidget(self.list)
        layout.addLayout(buttons)

        self.list.itemDoubleClicked.connect(lambda *_: self.settings())
        self.list.itemSelectionChanged.connect(self._sync_buttons)
        worker.samples_changed.connect(self.show_counts)
        self._sync_buttons()

    def _sync_buttons(self) -> None:
        """per gesture buttons only light up while a gesture is selected"""
        on = bool(self.list.selectedItems())
        for button in self.needs_selection:
            button.setEnabled(on)

    def show_counts(self, counts: dict[str, int]) -> None:
        self.names = list(counts)
        self.list.clear()
        cfg = self.worker.cfg
        gamepad = cfg.app.mode == "gamepad"
        self._set_columns(["gesture", *SIDES] if gamepad else ["gesture", "mode"])

        for name, n in counts.items():
            if gamepad:
                cells = [binding_text(cfg.gamepad.bindings, name, side) for side in SIDES]
            else:
                cells = [mode_summary(cfg.gestures, name)]
            item = QTreeWidgetItem([name, *cells])
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsDropEnabled)  # dropping onto a row would nest it
            item.setToolTip(0, f"{n} samples")
            for col in range(1, len(cells) + 1):
                item.setToolTip(col, item.text(col))
            self.list.addTopLevelItem(item)

        self._sync_buttons()

    def _set_columns(self, labels: list[str]) -> None:
        """name column fits its text, the rest share the width"""
        self.list.setColumnCount(len(labels))  # header labels alone never drop a column
        self.list.setHeaderLabels(labels)
        header = self.list.header()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        for col in range(1, len(labels)):
            header.setSectionResizeMode(col, QHeaderView.ResizeMode.Stretch)

    def _reordered(self, names: list[str]) -> None:
        self.names = names
        self.worker.reorder(names)

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

        if self.worker.cfg.app.mode == "gamepad":
            pad = PadBindingDialog(self.worker.cfg, name, self)
            if pad.exec():
                self.worker.set_bindings(name, pad.result_bindings())
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
