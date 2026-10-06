from PySide6.QtWidgets import QComboBox

from handing.output.macro import MACRO_PREFIX, Step, check_action

COMMON = ["click:left", "click:right", "double_click:left", "click:middle", "pgup", "pgdn", "ctrl+win+left", "ctrl+win+right", "alt+tab", "volume_up", "volume_down", "mute", "play_pause", "next_track", "prev_track"]

class ActionEdit(QComboBox):
    """editable combo for a key combo or macro:name, red border when invalid"""

    def __init__(self, macros: dict[str, list[Step]], optional: bool = True):
        super().__init__()
        self.macros = macros
        self.optional = optional

        self.setEditable(True)
        self.addItems([""] if optional else [])
        self.addItems([MACRO_PREFIX + name for name in macros] + COMMON)
        self.setCurrentText("")
        self.editTextChanged.connect(self._check)
        self._check()

    def action(self) -> str | None:
        text = self.currentText().strip()
        return text or None

    def set_action(self, action: str | None) -> None:
        self.setCurrentText(action or "")

    def error(self) -> str | None:
        action = self.action()
        if action is None:
            return None if self.optional else "action is required"

        try:
            check_action(action, self.macros)
        except ValueError as e:
            return str(e)

        return None

    def _check(self) -> None:
        error = self.error()
        self.setToolTip(error or "")
        self.setStyleSheet("QComboBox { border: 1px solid #c33; }" if error else "")
