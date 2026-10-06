from PySide6.QtCore import QThread, Signal

from handing.config.schema import Config
from handing.output.estop import EmergencyStop
from handing.output.keyboard import Keyboard
from handing.output.mouse import Mouse
from handing.pipeline.runner import Runner
from handing.recognition.samples import SampleSet

class Worker(QThread):
    """runs the pipeline off the ui thread, output starts disabled"""

    tick = Signal(object)  # pipeline.runner.Tick
    output_changed = Signal(bool)  # True when output is live
    failed = Signal(str)

    def __init__(self, cfg: Config, samples: SampleSet):
        super().__init__()
        self.cfg = cfg
        self.samples = samples
        self.estop = EmergencyStop(cfg.safety.estop_hotkey, on_change = lambda s: self.output_changed.emit(not s))
        self.estop.set_stopped(True)

    def set_output(self, live: bool) -> None:
        self.estop.set_stopped(not live)

    def run(self) -> None:
        keyboard, mouse = Keyboard(self.estop), Mouse(self.estop)

        try:
            with self.estop, Runner(self.cfg, keyboard, mouse, self.samples) as runner:
                while not self.isInterruptionRequested():
                    tick = runner.step()
                    if tick:
                        self.tick.emit(tick)
        except Exception as e:
            self.failed.emit(str(e))

    def stop(self) -> None:
        self.requestInterruption()
        self.wait(3000)
