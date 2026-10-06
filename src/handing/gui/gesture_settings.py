from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QDialog, QDialogButtonBox, QDoubleSpinBox, QFormLayout,
    QLabel, QMessageBox, QStackedWidget, QVBoxLayout, QWidget,
)

from handing.config.schema import DIRECTIONS, MODES, Config, GestureConfig
from handing.gui.action_edit import ActionEdit
from handing.output.macro import parse_macro

NONE = "(none)"
HINTS = {
    NONE: "recognized, but does nothing",
    "mouse": "hand movement moves the cursor\nsensitivity and deadzone are global, in config.yaml",
    "lock": "locks control until the unlock gesture is held",
}

def form_page(*rows) -> QWidget:
    page = QWidget()
    form = QFormLayout(page)
    for label, widget in rows:
        form.addRow(label, widget)

    return page

def spin(low: float, high: float, step: float) -> QDoubleSpinBox:
    box = QDoubleSpinBox()
    box.setRange(low, high)
    box.setSingleStep(step)

    return box

class GestureSettings(QDialog):
    """choose a mode and its options for one gesture"""

    def __init__(self, cfg: Config, name: str, parent = None):
        super().__init__(parent)
        self.setWindowTitle(f"settings: {name}")
        macros = {n: parse_macro(steps) for n, steps in cfg.macros.items()}
        current = cfg.gestures.get(name)

        self.mode = QComboBox()
        self.mode.addItems([NONE, *MODES])
        self.pages = QStackedWidget()
        self.sensitivity = spin(0.1, 10, 0.1)
        self.threshold = spin(0.05, 0.5, 0.01)
        self.directions = {d: ActionEdit(macros) for d in DIRECTIONS}
        self.action = ActionEdit(macros, optional = False)
        self.repeat = QCheckBox("repeat while held")

        for mode in (NONE, *MODES):
            if mode == "scroll":
                page = form_page(("sensitivity", self.sensitivity))
            elif mode == "trigger":
                page = form_page(("threshold (frame width)", self.threshold), *self.directions.items())
            elif mode == "action":
                page = form_page(("action", self.action), ("", self.repeat))
            else:
                page = form_page(("", QLabel(HINTS[mode])))
            self.pages.addWidget(page)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(form_page(("mode", self.mode)))
        layout.addWidget(self.pages)
        layout.addWidget(buttons)

        self.mode.currentIndexChanged.connect(self.pages.setCurrentIndex)
        self._load(current or GestureConfig(NONE))

    def _load(self, g: GestureConfig) -> None:
        self.mode.setCurrentText(g.mode)
        self.pages.setCurrentIndex(self.mode.currentIndex())
        self.sensitivity.setValue(g.sensitivity)
        self.threshold.setValue(g.threshold)
        for d, edit in self.directions.items():
            edit.set_action(getattr(g, d))
        self.action.set_action(g.action)
        self.repeat.setChecked(g.repeat)

    def result_gesture(self) -> GestureConfig | None:
        mode = self.mode.currentText()
        if mode == NONE:
            return None

        g = GestureConfig(mode)
        if mode == "scroll":
            g.sensitivity = self.sensitivity.value()
        elif mode == "trigger":
            g.threshold = self.threshold.value()
            for d, edit in self.directions.items():
                setattr(g, d, edit.action())
        elif mode == "action":
            g.action = self.action.action()
            g.repeat = self.repeat.isChecked()

        return g

    def _error(self) -> str | None:
        mode = self.mode.currentText()
        if mode == "action":
            return self.action.error()

        if mode == "trigger":
            errors = [e.error() for e in self.directions.values()]
            if not any(e.action() for e in self.directions.values()):
                return "set at least one direction"
            return next((e for e in errors if e), None)

        return None

    def accept(self) -> None:
        error = self._error()
        if error:
            QMessageBox.warning(self, self.windowTitle(), error)
            return

        super().accept()
