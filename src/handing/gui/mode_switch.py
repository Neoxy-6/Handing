from PySide6.QtCore import Signal
from PySide6.QtWidgets import QButtonGroup, QFrame, QHBoxLayout, QPushButton

from handing.config.schema import APP_MODES

class ModeSwitch(QFrame):
    """standard | gamepad, the lit half is the running mode"""

    picked = Signal(str)

    def __init__(self, mode: str):
        super().__init__()
        self.setObjectName("segments")
        self.buttons: dict[str, QPushButton] = {}
        group = QButtonGroup(self)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(3, 3, 3, 3)
        layout.setSpacing(3)

        for name in APP_MODES:
            button = QPushButton(name)
            button.setCheckable(True)
            button.setProperty("role", "segment")
            button.clicked.connect(lambda _, n = name: self.picked.emit(n))
            group.addButton(button)
            layout.addWidget(button, 1)
            self.buttons[name] = button

        self.show_mode(mode)

    def show_mode(self, mode: str) -> None:
        self.buttons[mode].setChecked(True)
