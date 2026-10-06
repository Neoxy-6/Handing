import copy

from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QDialog, QDialogButtonBox, QDoubleSpinBox, QFormLayout,
    QLabel, QLineEdit, QMessageBox, QSpinBox, QTabWidget, QVBoxLayout, QWidget,
)

from handing.config.schema import CONTROL_HANDS, POINTS, Config
from handing.config.lint import new_warnings
from handing.config.validate import validate
from handing.gui.confirm import confirm_warnings

def int_box(low: int, high: int) -> QSpinBox:
    box = QSpinBox()
    box.setRange(low, high)

    return box

def float_box(low: float, high: float, step: float, decimals: int = 2) -> QDoubleSpinBox:
    box = QDoubleSpinBox()
    box.setRange(low, high)
    box.setSingleStep(step)
    box.setDecimals(decimals)

    return box

def choice(*options) -> QComboBox:
    box = QComboBox()
    box.addItems([str(o) for o in options])

    return box

def get_value(widget, old):
    """read a widget back as the type of the old config value"""
    if isinstance(widget, QCheckBox):
        return widget.isChecked()
    if isinstance(widget, (QSpinBox, QDoubleSpinBox)):
        return widget.value()
    if isinstance(widget, QComboBox):
        return type(old)(widget.currentText())

    return widget.text().strip()

def set_value(widget, value) -> None:
    if isinstance(widget, QCheckBox):
        widget.setChecked(value)
    elif isinstance(widget, (QSpinBox, QDoubleSpinBox)):
        widget.setValue(value)
    elif isinstance(widget, QComboBox):
        widget.setCurrentText(str(value))
    else:
        widget.setText(str(value))

def pages(gesture_names: list[str]) -> list:
    """tab title, note, rows of (section, field, label, tooltip, widget)"""
    return [
        ("camera", "reopens the camera", [
            ("camera", "index", "camera", "camera index, 0 is the first one", int_box(0, 9)),
            ("camera", "mirrored", "mirrored", "the frame is already flipped like a mirror", QCheckBox()),
            ("camera", "idle_fps", "idle fps", "frames per second while no hand is seen, 0 = never slow down", int_box(0, 30)),
            ("detection", "hands", "hands", "how many hands to detect", choice(1, 2)),
            ("detection", "control_hand", "control hand", "only this hand controls, the other is ignored", choice(*CONTROL_HANDS)),
            ("detection", "min_confidence", "confidence", "minimum detection confidence", float_box(0.1, 0.95, 0.05)),
        ]),
        ("cursor", "", [
            ("cursor", "point", "point", "the part of the hand that drives the cursor", choice(*POINTS)),
            ("mouse", "sensitivity", "sensitivity", "1 = moving across the whole frame crosses the whole screen", float_box(0.2, 10, 0.1)),
            ("mouse", "deadzone", "deadzone", "camera px per frame ignored, stops jitter", float_box(0, 5, 0.1)),
            ("cursor", "min_cutoff", "smoothing", "one euro min cutoff, lower is smoother but laggier", float_box(0.05, 5, 0.05)),
            ("cursor", "beta", "speed boost", "one euro beta, higher follows fast moves better", float_box(0, 0.2, 0.005, 3)),
            ("cursor", "joystick_deadzone", "stick deadzone", "joystick: share of the stick radius around the center that does nothing", float_box(0, 0.5, 0.01)),
            ("cursor", "joystick_speed", "stick speed", "joystick: cursor speed in screen px per second at full push", float_box(100, 6000, 100, 0)),
            ("cursor", "joystick_curve", "stick curve", "joystick: 1 = linear, higher = slower and finer near the center", float_box(1, 4, 0.1)),
        ]),
        ("gestures", "", [
            ("recognition", "max_distance", "max distance", "farther than this from every sample counts as unknown", float_box(0.5, 5, 0.1)),
            ("recognition", "k", "k", "neighbors that vote", int_box(1, 15)),
            ("stability", "enter_frames", "enter frames", "frames a gesture must hold before it switches", int_box(1, 30)),
            ("stability", "exit_frames", "exit frames", "frames a gesture may be missing before it ends", int_box(1, 60)),
            ("stability", "min_confidence", "min confidence", "share of neighbor votes needed to switch", float_box(0.2, 1, 0.05)),
            ("keyboard", "repeat_ms", "repeat ms", "interval of repeated actions while a gesture is held", int_box(50, 3000)),
        ]),
        ("safety", "stop key applies after restart", [
            ("safety", "lock", "lock", "start locked, hold the unlock gesture to begin, lock again when the hand leaves", QCheckBox()),
            ("safety", "unlock_gesture", "unlock", "hold this gesture to unlock control", choice(*gesture_names)),
            ("safety", "unlock_frames", "unlock frames", "frames the unlock gesture must hold", int_box(1, 90)),
            ("safety", "estop_hotkey", "stop key", "turns output on / off from anywhere, like <ctrl>+<alt>+q", QLineEdit()),
            ("ui", "overlay", "overlay", "status pill while the window is hidden", QCheckBox()),
        ]),
    ]

class SettingsDialog(QDialog):
    """edits a copy of the config, validated before it is accepted"""

    def __init__(self, cfg: Config, gesture_names: list[str], parent = None):
        super().__init__(parent)
        self.setWindowTitle("settings")
        self.cfg = cfg
        self.gesture_names = gesture_names
        self.rows = []
        self.labels = {}

        tabs = QTabWidget()
        for title, note, rows in pages(gesture_names):
            page = QWidget()
            form = QFormLayout(page)
            for section, name, label, tip, widget in rows:
                set_value(widget, getattr(getattr(cfg, section), name))
                widget.setToolTip(tip)
                form.addRow(label, widget)
                self.labels[widget] = form.labelForField(widget)
                self.labels[widget].setToolTip(tip)
                self.rows.append((section, name, widget))
            if note:
                form.addRow(QLabel(note))
            tabs.addTab(page, title)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(tabs)
        layout.addWidget(buttons)

        widgets = {(section, name): widget for section, name, widget in self.rows}
        self._hands = widgets["detection", "hands"]
        self._control = widgets["detection", "control_hand"]
        self._control.currentTextChanged.connect(self._sync_hands)
        self._sync_hands(self._control.currentText())

        lock = widgets["safety", "lock"]
        unlock_rows = [widgets["safety", "unlock_gesture"], widgets["safety", "unlock_frames"]]
        lock.toggled.connect(lambda on: [self._enable(w, on) for w in unlock_rows])
        lock.toggled.emit(lock.isChecked())

    def _sync_hands(self, control: str) -> None:
        """one hand controls; the runner still detects two internally to find it"""
        locked = control != "any"
        if locked:
            self._hands.setCurrentText("1")

        self._enable(self._hands, not locked)
        self._hands.setToolTip(f"only the {control} hand controls" if locked else "how many hands to detect")

    def _enable(self, widget, on: bool) -> None:
        """grey out the label too, so the row clearly reads as off"""
        widget.setEnabled(on)
        self.labels[widget].setEnabled(on)

    def result_config(self) -> Config:
        new = copy.deepcopy(self.cfg)

        for section, name, widget in self.rows:
            part = getattr(new, section)
            setattr(part, name, get_value(widget, getattr(part, name)))

        return new

    def accept(self) -> None:
        new = self.result_config()
        try:
            validate(new)
        except ValueError as e:
            QMessageBox.warning(self, "settings", str(e))
            return

        if confirm_warnings(self, "settings", new_warnings(self.cfg, new, self.gesture_names)):
            super().accept()
