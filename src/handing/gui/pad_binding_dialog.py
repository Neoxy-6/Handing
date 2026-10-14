from PySide6.QtCore import Qt
from PySide6.QtWidgets import QCheckBox, QComboBox, QDialog, QDialogButtonBox, QGridLayout, QLabel, QVBoxLayout

from handing.config.keys import SIDES, resolve
from handing.config.schema import PAD_BUTTONS, PAD_TRIGGERS, Config, PadBinding

NONE = "-"

class PadBindingDialog(QDialog):
    """the button each hand holds while it shows one gesture"""

    def __init__(self, cfg: Config, name: str, parent = None):
        super().__init__(parent)
        self.setWindowTitle(f"gamepad: {name}")
        self.buttons: dict[str, QComboBox] = {}
        self.repeats: dict[str, QCheckBox] = {}
        bindings = cfg.gamepad.bindings

        grid = QGridLayout()
        grid.setHorizontalSpacing(16)
        grid.setVerticalSpacing(10)
        for col, text in ((1, "button"), (2, "repeat")):
            head = QLabel(text)
            head.setProperty("role", "muted")
            grid.addWidget(head, 0, col)

        for row, side in enumerate(SIDES, 1):
            binding = bindings.get(resolve(bindings, name, side))
            button = QComboBox()
            button.addItems([NONE, *PAD_TRIGGERS, *PAD_BUTTONS])
            button.setCurrentText(binding.button if binding else NONE)
            button.setMinimumWidth(120)
            repeat = QCheckBox()
            repeat.setChecked(bool(binding and binding.repeat))
            repeat.setToolTip(f"press and release every {cfg.keyboard.repeat_ms} ms while held, set in settings > gestures > repeat ms")
            button.currentTextChanged.connect(lambda text, r = repeat: r.setEnabled(text != NONE))
            repeat.setEnabled(button.currentText() != NONE)

            grid.addWidget(QLabel(side), row, 0)
            grid.addWidget(button, row, 1)
            grid.addWidget(repeat, row, 2, Qt.AlignmentFlag.AlignCenter)
            self.buttons[side], self.repeats[side] = button, repeat

        hint = QLabel("held while the gesture is, both sticks follow the palms either way")
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
        """side -> binding, None where the hand presses nothing"""
        out = {}
        for side in SIDES:
            text = self.buttons[side].currentText()
            out[side] = PadBinding(text, self.repeats[side].isChecked()) if text != NONE else None

        return out
