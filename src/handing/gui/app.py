import sys

from PySide6.QtWidgets import QApplication, QMessageBox

from handing.config import loader
from handing.core import paths
from handing.gui.main_window import MainWindow
from handing.gui.worker import Worker
from handing.recognition.samples import SampleSet

def main() -> int:
    app = QApplication(sys.argv)

    try:
        cfg = loader.load()
    except ValueError as e:
        QMessageBox.critical(None, "Handing", f"config error in {paths.config_path()}:\n\n{e}")
        return 1

    worker = Worker(cfg, SampleSet.load(paths.default_gestures()))
    window = MainWindow(worker)
    window.show()
    worker.start()

    return app.exec()
