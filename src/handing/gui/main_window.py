from PySide6.QtCore import QEvent, QTimer, Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QMainWindow, QMessageBox, QPushButton, QVBoxLayout, QWidget

from handing.gui.frame_view import FrameView
from handing.gui.gesture_panel import GesturePanel
from handing.control.modes.build import stick_area
from handing.control.states import State
from handing.features import anchor
from handing.gui.render import draw_hands, draw_stick
from handing.gui.settings_dialog import SettingsDialog
from handing.gui.status_card import StatusCard
from handing.gui.style import set_role
from handing.gui.worker import Worker

def pretty_hotkey(hotkey: str) -> str:
    """'<ctrl>+<alt>+q' -> 'Ctrl+Alt+Q'"""
    return "+".join(k.strip("<>").capitalize() for k in hotkey.split("+"))

class MainWindow(QMainWindow):
    visibility_changed = Signal(bool)
    quit_requested = Signal()

    def __init__(self, worker: Worker):
        super().__init__()
        self.setWindowTitle("Handing")
        self.resize(960, 540)

        self.worker = worker
        self.quitting = False  # set before QApplication.quit so close really closes
        self.view = FrameView()
        self.status = StatusCard()
        self.output = QPushButton()
        self.output.setCheckable(True)
        self.output.setMinimumHeight(36)

        settings = QPushButton("settings")
        settings.setMinimumHeight(36)
        settings.clicked.connect(self.open_settings)
        hint = QLabel(f"{pretty_hotkey(worker.cfg.safety.estop_hotkey)}  on / off")
        hint.setProperty("role", "muted")
        hint.setWordWrap(True)

        bottom = QHBoxLayout()
        bottom.addWidget(settings, 1)
        bottom.addWidget(self.output, 1)

        side = QVBoxLayout()
        side.setSpacing(10)
        side.addWidget(self.status)
        side.addWidget(GesturePanel(worker), 1)
        side.addWidget(hint)
        side.addLayout(bottom)

        panel = QWidget()
        panel.setFixedWidth(300)
        panel.setLayout(side)

        root = QHBoxLayout()
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(12)
        root.addWidget(self.view, 1)
        root.addWidget(panel)

        central = QWidget()
        central.setLayout(root)
        self.setCentralWidget(central)

        self.output.toggled.connect(worker.set_output)
        worker.output_changed.connect(self.on_output_changed)
        worker.tick.connect(self.on_tick)
        worker.failed.connect(self.on_failed)
        self.on_output_changed(False)

    def on_tick(self, tick) -> None:
        if not self.isVisible():
            return

        frame = draw_hands(tick.frame.copy(), tick.hands)
        self._draw_stick(frame, tick)
        self.view.show_frame(frame)
        self.status.update_tick(tick)

    def _draw_stick(self, frame, tick) -> None:
        """show the joystick guide while a joystick gesture runs"""
        cfg = self.worker.cfg
        g = cfg.gestures.get(tick.status.gesture or "")
        if tick.status.state != State.ACTIVE or g is None or g.mode != "joystick":
            return

        center, radius = stick_area(cfg)
        point_of = anchor.palm_center if cfg.cursor.point == "palm" else anchor.index_tip
        point = point_of(tick.hand) * (tick.hands.width, tick.hands.height) if tick.hand else None
        draw_stick(frame, center, radius, cfg.cursor.joystick_deadzone, point)

    def on_output_changed(self, live: bool) -> None:
        self.output.blockSignals(True)
        self.output.setChecked(live)
        self.output.blockSignals(False)

        self.output.setText("ON" if live else "OFF")
        set_role(self.output, "danger" if live else "")

    def open_settings(self) -> None:
        dialog = SettingsDialog(self.worker.cfg, self.worker.editor.samples.names, self)
        if dialog.exec():
            self.worker.apply_config(dialog.result_config())

    def on_failed(self, message: str) -> None:
        QMessageBox.critical(self, "Handing", message)

    def showEvent(self, event) -> None:
        self.visibility_changed.emit(True)
        super().showEvent(event)

    def hideEvent(self, event) -> None:
        if not self.quitting:
            self.visibility_changed.emit(False)
        super().hideEvent(event)

    def changeEvent(self, event) -> None:
        """minimize hides to the tray"""
        if event.type() == QEvent.Type.WindowStateChange and self.isMinimized():
            QTimer.singleShot(0, self.hide)

        super().changeEvent(event)

    def closeEvent(self, event) -> None:
        """x quits the whole app, the tray does the cleanup"""
        if self.quitting:
            super().closeEvent(event)
            return

        event.ignore()
        self.quit_requested.emit()
