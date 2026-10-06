import copy

from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QDialog, QDialogButtonBox, QDoubleSpinBox, QFormLayout,
    QLabel, QLineEdit, QMessageBox, QSpinBox, QTabWidget, QVBoxLayout, QWidget,
)

from handing.config.schema import CONTROL_HANDS, POINTS, Config
from handing.config.validate import validate

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
    """tab title, note, rows of (section, field, label, widget)"""
    return [
        ("camera", "changes reopen the camera", [
            ("camera", "index", "camera index", int_box(0, 9)),
            ("camera", "mirrored", "frame is mirrored", QCheckBox()),
            ("camera", "idle_fps", "fps with no hand (0 = off)", int_box(0, 30)),
            ("detection", "hands", "hands", choice(1, 2)),
            ("detection", "control_hand", "control hand", choice(*CONTROL_HANDS)),
            ("detection", "min_confidence", "detection confidence", float_box(0.1, 0.95, 0.05)),
        ]),
        ("cursor", "", [
            ("cursor", "point", "tracking point", choice(*POINTS)),
            ("mouse", "sensitivity", "sensitivity", float_box(0.2, 10, 0.1)),
            ("mouse", "deadzone", "deadzone (px / frame)", float_box(0, 5, 0.1)),
            ("cursor", "min_cutoff", "smoothing min cutoff", float_box(0.05, 5, 0.05)),
            ("cursor", "beta", "smoothing beta", float_box(0, 0.2, 0.005, 3)),
        ]),
        ("recognition", "", [
            ("recognition", "max_distance", "unknown distance", float_box(0.5, 5, 0.1)),
            ("recognition", "k", "neighbors (k)", int_box(1, 15)),
            ("stability", "enter_frames", "frames to enter", int_box(1, 30)),
            ("stability", "exit_frames", "frames to leave", int_box(1, 60)),
            ("stability", "min_confidence", "confidence to enter", float_box(0.2, 1, 0.05)),
            ("keyboard", "repeat_ms", "repeat interval (ms)", int_box(50, 3000)),
        ]),
        ("safety", "the stop hotkey applies after restarting Handing", [
            ("safety", "unlock_gesture", "unlock gesture", choice(*gesture_names)),
            ("safety", "unlock_frames", "frames to unlock", int_box(1, 90)),
            ("safety", "estop_hotkey", "stop hotkey", QLineEdit()),
            ("ui", "overlay", "status overlay when hidden", QCheckBox()),
        ]),
    ]

class SettingsDialog(QDialog):
    """edits a copy of the config, validated before it is accepted"""

    def __init__(self, cfg: Config, gesture_names: list[str], parent = None):
        super().__init__(parent)
        self.setWindowTitle("settings")
        self.cfg = cfg
        self.rows = []

        tabs = QTabWidget()
        for title, note, rows in pages(gesture_names):
            page = QWidget()
            form = QFormLayout(page)
            for section, name, label, widget in rows:
                set_value(widget, getattr(getattr(cfg, section), name))
                form.addRow(label, widget)
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

    def result_config(self) -> Config:
        new = copy.deepcopy(self.cfg)

        for section, name, widget in self.rows:
            part = getattr(new, section)
            setattr(part, name, get_value(widget, getattr(part, name)))

        return new

    def accept(self) -> None:
        try:
            validate(self.result_config())
        except ValueError as e:
            QMessageBox.warning(self, "settings", str(e))
            return

        super().accept()
