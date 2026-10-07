import ctypes
import sys

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QMessageBox

from handing.config import loader
from handing.core import paths
from handing.gui.main_window import MainWindow
from handing.gui.overlay import Overlay
from handing.gui.style import SHEET
from handing.gui.tray import Tray
from handing.gui.worker import Worker
from handing.pipeline.gesture_editor import GestureEditor
from handing.recognition.samples import SampleSet

def load_samples() -> SampleSet:
    """user samples, seeded from the bundled defaults on first run"""
    path = paths.user_gestures()
    if path.exists():
        return SampleSet.load(path)

    samples = SampleSet.load(paths.default_gestures())
    samples.save(path)

    return samples

def own_taskbar_entry() -> None:
    """without this windows groups the window under python.exe and shows its icon"""
    if sys.platform == "win32":
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("Handing.App")

def main() -> int:
    own_taskbar_entry()
    app = QApplication(sys.argv)
    app.setApplicationName("Handing")
    app.setWindowIcon(QIcon(str(paths.app_icon())))
    app.setQuitOnLastWindowClosed(False)
    app.setStyleSheet(SHEET)

    try:
        cfg = loader.load()
    except ValueError as e:
        QMessageBox.critical(None, "Handing", f"config error in {paths.config_path()}:\n\n{e}")
        return 1

    worker = Worker(GestureEditor(load_samples(), cfg, paths.user_gestures()))
    window = MainWindow(worker)
    tray = Tray(window, worker)
    tray.show()
    window.quit_requested.connect(tray.quit)
    overlay = Overlay(worker)
    window.visibility_changed.connect(lambda visible: overlay.set_enabled(not visible and cfg.ui.overlay))
    window.show()
    worker.start()

    return app.exec()
