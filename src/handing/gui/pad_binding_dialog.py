from PySide6.QtCore import Qt
from PySide6.QtWidgets import QCheckBox, QComboBox, QDialog, QDialogButtonBox, QGridLayout, QLabel, QVBoxLayout

from handing.config.keys import SIDES, resolve
from handing.config.schema import PAD_BUTTONS, PAD_TRIGGERS, Config, PadBinding

NONE = "-"

class PadBindingDialog(QDialog):
    """what each hand does while it shows one gesture: hold a button, repeat it, drive its stick"""

    def __init__(self, cfg: Config, name: str, parent = None):
        super().__init__(parent)
        self.setWindowTitle(f"gamepad: {name}")
        self.buttons: dict[str, QComboBox] = {}
        self.repeats: dict[str, QCheckBox] = {}
        self.sticks: dict[str, QCheckBox] = {}
        bindings = cfg.gamepad.bindings

        grid = QGridLayout()
        grid.setHorizontalSpacing(16)
        grid.setVerticalSpacing(10)
        for col, text in ((1, "button"), (2, "repeat"), (3, "stick")):
            head = QLabel(text)
            head.setProperty("role", "muted")
            grid.addWidget(head, 0, col)

        for row, side in enumerate(SIDES, 1):
            binding = bindings.get(resolve(bindings, name, side))
            button = QComboBox()
            button.addItems([NONE, *PAD_TRIGGERS, *PAD_BUTTONS])
            button.setCurrentText(binding.button if binding and binding.button else NONE)
            button.setMinimumWidth(120)
            repeat = QCheckBox()
            repeat.setChecked(bool(binding and binding.repeat))
            repeat.setToolTip(f"press and release every {cfg.keyboard.repeat_ms} ms while held, set in settings > gestures > repeat ms")
            button.currentTextChanged.connect(lambda text, r = repeat: r.setEnabled(text != NONE))
            repeat.setEnabled(button.currentText() != NONE)
            stick = QCheckBox()
            stick.setChecked(bool(binding and binding.stick))
            stick.setToolTip("with settings > gamepad > sticks set to gesture, this hand drives its stick only while this gesture is held")

            grid.addWidget(QLabel(side), row, 0)
            grid.addWidget(button, row, 1)
            grid.addWidget(repeat, row, 2, Qt.AlignmentFlag.AlignCenter)
            grid.addWidget(stick, row, 3, Qt.AlignmentFlag.AlignCenter)
            self.buttons[side], self.repeats[side], self.sticks[side] = button, repeat, stick

        mode = cfg.gamepad.sticks
        hint = QLabel("stick only counts while settings > gamepad > sticks is gesture" if mode != "gesture" else "a hand drives its stick only while a gesture with stick is held")
        hint.setProperty("role", "muted")

        ok = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        ok.accepted.connect(self.accept)
        ok.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 14)
        layout.setSpacing(14)
        layout.addLayout(grid)
        layout.addWidget(hint)
        layout.addWidget(ok)

    def result_bindings(self) -> dict[str, PadBinding | None]:
        """side -> binding, None where the hand does nothing"""
        out = {}
        for side in SIDES:
            text = self.buttons[side].currentText()
            button = text if text != NONE else None
            stick = self.sticks[side].isChecked()
            out[side] = PadBinding(button, bool(button) and self.repeats[side].isChecked(), stick) if button or stick else None

        return out
