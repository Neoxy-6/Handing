import copy

from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QDialog, QDialogButtonBox, QDoubleSpinBox, QFormLayout,
    QLabel, QMessageBox, QStackedWidget, QVBoxLayout, QWidget,
)

from handing.config.keys import make_key
from handing.config.lint import new_warnings
from handing.config.schema import CONTROL_HANDS, DIRECTIONS, MODES, STYLES_FOR, Config, GestureConfig
from handing.config.validate import validate
from handing.gui.action_edit import ActionEdit
from handing.gui.confirm import confirm_warnings
from handing.output.macro import parse_macro

NONE = "(none)"
NONE_HINTS = {
    "any": "recognized, but does nothing",
    "side": "no override, this hand uses the 'any' setting",
}
STYLE_TIPS = {
    "mouse": "relative: follows hand movement / joystick: distance from the stick center sets the speed",
    "drag": "relative: follows hand movement / joystick: distance from the stick center sets the speed",
}
HINTS = {
    "mouse": "moves the cursor\nspeed and stick settings are in settings > cursor",
    "drag": "moves the cursor with the left button held\nlets go when the gesture ends",
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

    def __init__(self, cfg: Config, name: str, gesture_names: list[str], parent = None):
        super().__init__(parent)
        self.setWindowTitle(f"settings: {name}")
        self.cfg = cfg
        self.name = name
        self.gesture_names = gesture_names
        macros = {n: parse_macro(steps) for n, steps in cfg.macros.items()}

        self.hand = QComboBox()
        self.hand.addItems(CONTROL_HANDS)
        control = cfg.detection.control_hand
        for i, hand in enumerate(CONTROL_HANDS):
            if control != "any" and hand not in ("any", control):
                self.hand.model().item(i).setEnabled(False)  # that hand never controls

        self.none_hint = QLabel(NONE_HINTS["any"])
        self.mode = QComboBox()
        self.style = QComboBox()
        self.mode.addItems([NONE, *MODES])
        if not cfg.safety.lock:
            self.mode.model().item(1 + MODES.index("lock")).setEnabled(False)  # locking is off in settings
        self.pages = QStackedWidget()
        self.sensitivity = spin(0.1, 10, 0.1)
        self.threshold = spin(0.05, 0.5, 0.01)
        self.directions = {d: ActionEdit(macros) for d in DIRECTIONS}
        self.action = ActionEdit(macros, optional = False)
        self.repeat = QCheckBox("repeat")

        for mode in (NONE, *MODES):
            if mode == "scroll":
                page = form_page(("sensitivity", self.sensitivity))
            elif mode == "trigger":
                page = form_page(("threshold", self.threshold), *self.directions.items())
            elif mode == "action":
                page = form_page(("action", self.action), ("", self.repeat))
            elif mode == NONE:
                page = form_page(("", self.none_hint))
            else:
                page = form_page(("", QLabel(HINTS[mode])))
            self.pages.addWidget(page)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(form_page(("hand", self.hand), ("mode", self.mode), ("style", self.style)))
        layout.addWidget(self.pages)
        layout.addWidget(buttons)

        self.mode.currentIndexChanged.connect(self.pages.setCurrentIndex)
        self.mode.currentTextChanged.connect(self._sync_style)
        self.hand.currentTextChanged.connect(self._load_hand)
        self._load_hand("any")

    def key(self) -> str:
        return make_key(self.name, self.hand.currentText())

    def _load_hand(self, hand: str) -> None:
        self.none_hint.setText(NONE_HINTS["any" if hand == "any" else "side"])
        self._load(self.cfg.gestures.get(self.key()) or GestureConfig(NONE))

    def _sync_style(self, mode: str, keep: str | None = None) -> None:
        """offer the styles this mode supports, keep the choice when it still fits"""
        styles = STYLES_FOR.get(mode, ())
        current = keep or self.style.currentText()

        self.style.blockSignals(True)
        self.style.clear()
        self.style.addItems(styles)
        if styles:
            self.style.setCurrentText(current if current in styles else styles[0])
        self.style.blockSignals(False)

        self.style.setEnabled(bool(styles))
        self.style.setToolTip(STYLE_TIPS.get(mode, ""))

    def _load(self, g: GestureConfig) -> None:
        self.mode.setCurrentText(g.mode)
        self._sync_style(g.mode, g.style)
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
        if mode in STYLES_FOR:
            g.style = self.style.currentText()
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
        candidate = copy.deepcopy(self.cfg)
        gesture = self.result_gesture()
        if gesture is None:
            candidate.gestures.pop(self.key(), None)
        else:
            candidate.gestures[self.key()] = gesture

        if not error:
            try:
                validate(candidate)
            except ValueError as e:
                error = str(e)

        if error:
            QMessageBox.warning(self, self.windowTitle(), error)
            return

        if confirm_warnings(self, self.windowTitle(), new_warnings(self.cfg, candidate, self.gesture_names)):
            super().accept()
