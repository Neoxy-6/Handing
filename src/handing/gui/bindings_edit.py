from PySide6.QtCore import Qt
from PySide6.QtWidgets import QComboBox, QFrame, QGridLayout, QLabel, QScrollArea, QWidget

from handing.config.keys import SIDES, make_key, resolve, split_key
from handing.config.schema import PAD_BUTTONS, PAD_TRIGGERS

NONE = "-"
VISIBLE_ROWS = 6  # more gestures scroll
ROW = 38  # picker height plus spacing

class BindingsEdit(QScrollArea):
    """a line per recorded gesture with a button picker per hand, spaced like the form above"""

    def __init__(self, bindings: dict[str, str], gesture_names: list[str]):
        super().__init__()
        self.kept = {k: v for k, v in bindings.items() if split_key(k)[0] not in gesture_names}  # no samples, not shown but not lost
        self.boxes: dict[tuple[str, str], QComboBox] = {}

        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(8)
        grid.setColumnStretch(1, 1)
        grid.setColumnStretch(2, 1)

        for col, side in enumerate(SIDES, 1):
            head = QLabel(side)
            head.setProperty("role", "muted")
            grid.addWidget(head, 0, col, Qt.AlignmentFlag.AlignCenter)

        for row, name in enumerate(gesture_names, 1):
            grid.addWidget(QLabel(name), row, 0)
            for col, side in enumerate(SIDES, 1):
                box = QComboBox()
                box.addItems([NONE, *PAD_TRIGGERS, *PAD_BUTTONS])
                box.setCurrentText(bindings.get(resolve(bindings, name, side), NONE))
                grid.addWidget(box, row, col)
                self.boxes[name, side] = box

        inner = QWidget()
        inner.setLayout(grid)
        self.setWidget(inner)
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setFixedHeight(inner.sizeHint().height() if len(gesture_names) <= VISIBLE_ROWS else ROW * (VISIBLE_ROWS + 1))

    def bindings(self) -> dict[str, str]:
        """always written per hand, a plain 'fist' key becomes fist@left and fist@right"""
        out = dict(self.kept)
        for (name, side), box in self.boxes.items():
            if box.currentText() != NONE:
                out[make_key(name, side)] = box.currentText()

        return out
