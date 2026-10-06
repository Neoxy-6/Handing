import queue

from PySide6.QtCore import QThread, Signal

from handing.config.schema import GestureConfig
from handing.features.normalize import normalize
from handing.output.estop import EmergencyStop
from handing.output.keyboard import Keyboard
from handing.output.mouse import Mouse
from handing.pipeline.gesture_editor import GestureEditor
from handing.pipeline.runner import Runner, Tick
from handing.recognition.similarity import find_similar

class Worker(QThread):
    """runs the pipeline off the ui thread, output starts disabled; gesture edits are queued and applied here"""

    tick = Signal(object)  # pipeline.runner.Tick
    output_changed = Signal(bool)  # True when output is live
    samples_changed = Signal(object)  # dict gesture name -> sample count
    record_progress = Signal(int)
    record_finished = Signal(str, object, object)  # name, poses, recognition.similarity.Similar | None
    failed = Signal(str)

    def __init__(self, editor: GestureEditor):
        super().__init__()
        self.editor = editor
        self.cfg = editor.cfg
        self.estop = EmergencyStop(self.cfg.safety.estop_hotkey, on_change = lambda s: self.output_changed.emit(not s))
        self.estop.set_stopped(True)

        self._jobs: queue.Queue = queue.Queue()
        self._record_name: str | None = None
        self._record_count = 0
        self._poses: list = []

    def set_output(self, live: bool) -> None:
        self.estop.set_stopped(not live)

    def record(self, name: str, count: int) -> None:
        self._jobs.put(lambda runner: self._start_record(name, count))

    def cancel_record(self) -> None:
        self._jobs.put(lambda runner: self._start_record(None, 0))

    def add_samples(self, name: str, poses: list) -> None:
        """called after the user reviewed a finished recording"""
        self._jobs.put(lambda runner: self._add(runner, name, poses))

    def delete(self, name: str) -> None:
        self._jobs.put(lambda runner: self._edit(runner, self.editor.delete, name))

    def rename(self, old: str, new: str) -> None:
        self._jobs.put(lambda runner: self._edit(runner, self.editor.rename, old, new))

    def configure(self, name: str, gesture: GestureConfig | None) -> None:
        self._jobs.put(lambda runner: self._edit(runner, self.editor.set_gesture, name, gesture))

    def run(self) -> None:
        keyboard, mouse = Keyboard(self.estop), Mouse(self.estop)

        try:
            with self.estop, Runner(self.cfg, keyboard, mouse, self.editor.samples) as runner:
                self.samples_changed.emit(self.editor.counts())

                while not self.isInterruptionRequested():
                    while not self._jobs.empty():
                        self._jobs.get()(runner)

                    tick = runner.step()
                    if tick:
                        self._collect(runner, tick)
                        self.tick.emit(tick)
        except Exception as e:
            self.failed.emit(str(e))

    def stop(self) -> None:
        self.requestInterruption()
        self.wait(3000)

    def _start_record(self, name: str | None, count: int) -> None:
        self._record_name, self._record_count, self._poses = name, count, []

    def _collect(self, runner: Runner, tick: Tick) -> None:
        if self._record_name is None or tick.hands.empty:
            return

        hands = tick.hands
        self._poses.append(normalize(hands.hands[0], hands.width, hands.height))
        self.record_progress.emit(len(self._poses))

        if len(self._poses) >= self._record_count:
            name, self._record_name = self._record_name, None
            rec = self.cfg.recognition
            similar = find_similar(self.editor.samples, name, self._poses, rec.k, rec.max_distance)
            self.record_finished.emit(name, self._poses, similar)

    def _add(self, runner: Runner, name: str, poses: list) -> None:
        self.editor.add(name, poses)
        self._refresh(runner)

    def _edit(self, runner: Runner, change, *args) -> None:
        change(*args)
        runner.rebuild_control()
        self._refresh(runner)

    def _refresh(self, runner: Runner) -> None:
        runner.classifier.update(self.editor.samples)
        self.samples_changed.emit(self.editor.counts())
