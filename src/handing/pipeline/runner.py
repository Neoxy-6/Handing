from dataclasses import dataclass

import numpy as np

from handing.config.keys import resolve
from handing.config.schema import Config
from handing.control.fsm import StateMachine
from handing.control.modes.base import Mode
from handing.control.modes.build import build_modes
from handing.control.states import State, Status
from handing.core import paths
from handing.core.clock import now_ms
from handing.core.types import Hand, HandFrame
from handing.detection.landmarker import Landmarker
from handing.features import anchor
from handing.filtering.hysteresis import Hysteresis
from handing.input import preprocess
from handing.input.camera import Camera
from handing.input.throttle import Throttle
from handing.output.macro import ActionRunner, parse_macro
from handing.output.screen import virtual_screen
from handing.recognition.classifier import Classifier, Prediction
from handing.recognition.samples import SampleSet

@dataclass(frozen = True)
class Tick:
    frame: np.ndarray  # bgr, resized to camera.width
    hands: HandFrame
    hand: Hand | None  # the hand in control, others are only drawn
    prediction: Prediction | None  # of that hand, before filtering
    status: Status

class Runner:
    """camera -> detection -> recognition -> filtering -> state machine -> modes, one frame per step()"""

    def __init__(self, cfg: Config, keyboard, mouse, samples: SampleSet):
        self.cfg = cfg
        self.camera = Camera(cfg.camera.index, mirror = cfg.camera.flip)
        self.throttle = Throttle(cfg.camera.idle_fps)
        num_hands = cfg.detection.hands if cfg.detection.control_hand == "any" else 2
        self.landmarker = Landmarker(paths.model_path(), num_hands, cfg.detection.min_confidence, cfg.camera.frame_mirrored)

        rec = cfg.recognition
        self.classifier = Classifier(samples, rec.k, rec.max_distance, rec.align_rotation)
        self.hyst = Hysteresis(cfg.stability.enter_frames, cfg.stability.exit_frames, cfg.stability.min_confidence)

        macros = {name: parse_macro(steps) for name, steps in cfg.macros.items()}
        self.actions = ActionRunner(keyboard, mouse, macros, cfg.keyboard.repeat_ms)
        self._mouse = mouse
        self._current: Mode | None = None
        self.rebuild_control()

    def rebuild_control(self) -> None:
        """apply changed gesture -> mode settings, also locks again"""
        self._switch(None, None, 0)
        safety = self.cfg.safety
        self.fsm = StateMachine({n: g.mode for n, g in self.cfg.gestures.items()}, safety.unlock_gesture, safety.unlock_frames, round(safety.lock_after * 1000), safety.lock)
        self.modes = build_modes(self.cfg, self._mouse, self.actions, virtual_screen().width)

    def step(self) -> Tick | None:
        """None when the camera gave no frame"""
        self.throttle.wait()
        frame = self.camera.read()
        if frame is None:
            return None

        t = now_ms()
        frame = preprocess.fit_width(frame, self.cfg.camera.width)
        hands = self.landmarker.detect(preprocess.to_rgb(frame), t)

        hand = self.pick(hands)
        if hand is None:
            self.hyst.reset()
            self._switch(None, None, t)
            return Tick(frame, hands, None, None, self.fsm.update(None, t))

        self.throttle.saw_hand()
        pred = self.classifier.predict(hand, hands.width, hands.height)
        stable = self.hyst.update(pred.name, pred.confidence)
        status = self.fsm.update(resolve(self.cfg.gestures, stable, hand.handedness), t)

        point = self._point(hand, hands, status.gesture)
        mode = self.modes.get(status.gesture) if status.state == State.ACTIVE else None

        if mode is self._current and mode:
            mode.update(point, t)
        else:
            self._switch(mode, point, t)

        return Tick(frame, hands, hand, pred, status)

    def pick(self, hands: HandFrame) -> Hand | None:
        """first hand matching detection.control_hand"""
        wanted = self.cfg.detection.control_hand

        return next((h for h in hands.hands if wanted == "any" or h.handedness.lower() == wanted), None)

    def _point(self, hand: Hand, hands: HandFrame, gesture: str | None) -> np.ndarray:
        """camera px, x toward the user's right, on the part of the hand this gesture follows"""
        g = self.cfg.gestures.get(gesture or "")
        point = anchor.of(hand, g.point if g else "palm") * (hands.width, hands.height)
        if not self.cfg.camera.frame_mirrored:
            point[0] = hands.width - point[0]

        return point

    def _switch(self, mode: Mode | None, point: np.ndarray | None, t: int) -> None:
        if self._current:
            self._current.exit()

        if mode:
            mode.enter(point, t)

        self._current = mode

    def open(self) -> None:
        self.camera.open()

    def close(self) -> None:
        self._switch(None, None, 0)
        self.camera.close()
        self.landmarker.close()

    def __enter__(self) -> "Runner":
        self.open()
        return self

    def __exit__(self, *_) -> None:
        self.close()
