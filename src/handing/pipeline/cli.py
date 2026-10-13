import argparse

from handing.config import loader
from handing.core import paths
from handing.output.dpi import enable_dpi_awareness
from handing.output.dry import DryOutput
from handing.output.estop import EmergencyStop
from handing.output.keyboard import Keyboard
from handing.output.mouse import Mouse
from handing.pipeline.capture import Capture
from handing.pipeline.dual import DualTracker, Side
from handing.pipeline.runner import Runner
from handing.recognition.classifier import Classifier
from handing.recognition.samples import SampleSet

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(prog = "handing", description = "gesture control in the terminal, dry run by default")
    p.add_argument("--live", action = "store_true", help = "really control the pc, ctrl+alt+q toggles stop")
    p.add_argument("--dual", action = "store_true", help = "only print what each hand shows, no output")
    p.add_argument("--gamepad", action = "store_true", help = "both hands drive a virtual xbox controller, --live sends it")

    return p.parse_args()

def status_line(tick, output) -> str:
    pred = tick.prediction
    raw = f"{pred.name:8} {pred.confidence:.2f} {pred.distance:4.2f}" if pred else f"{'-':8} {'':4} {'':4}"
    state = f"{tick.status.state.value:8} {tick.status.gesture or '':8}"

    return f"{state} | raw {raw} | {output}"

def side_text(side: Side) -> str:
    if side.hand is None:
        return f"{'-':8} {'':4} {'':11}"

    x, y = side.point

    return f"{side.gesture:8} {side.prediction.confidence:.2f} ({x:4.0f},{y:4.0f})"

def load_samples() -> SampleSet:
    """the user's gestures like the gui uses, the bundled ones before the first run"""
    path = paths.user_gestures()

    return SampleSet.load(path if path.exists() else paths.default_gestures())

def run_dual(cfg, samples: SampleSet) -> None:
    rec = cfg.recognition
    tracker = DualTracker(cfg, Classifier(samples, rec.k, rec.max_distance, rec.align_rotation))
    capture = Capture(cfg, 2)
    capture.open()

    try:
        while True:
            read = capture.read()
            if read is None:
                continue

            sides = tracker.update(read[1])
            if any(s.hand for s in sides.values()):
                capture.saw_hand()

            print(f"\rL {side_text(sides['left'])} | R {side_text(sides['right'])}", end = "", flush = True)
    except KeyboardInterrupt:
        print()
    finally:
        capture.close()

def run_gamepad(cfg, estop: EmergencyStop, live: bool) -> None:
    from handing.gamepad.pad import DryPad, XboxPad, describe
    from handing.gamepad.runner import GamepadRunner

    pad = XboxPad(estop) if live else DryPad()

    with estop, GamepadRunner(cfg, pad, load_samples()) as runner:
        try:
            while True:
                tick = runner.step()
                if tick:
                    gestures = " ".join(f"{side[0].upper()} {s.gesture if s.hand else '-':8}" for side, s in tick.sides.items())
                    print(f"\r{gestures} | {describe(tick.pad):<40}", end = "", flush = True)
        except KeyboardInterrupt:
            print()

def main() -> None:
    args = parse_args()
    enable_dpi_awareness()
    cfg = loader.load()

    if args.dual:
        print(f"both hands, config {paths.config_path()}, ctrl+c to quit")
        return run_dual(cfg, load_samples())

    estop = EmergencyStop(cfg.safety.estop_hotkey, on_change = lambda s: print("\nSTOPPED" if s else "\nrunning"))
    if args.live:
        keyboard, mouse = Keyboard(estop), Mouse(estop)
    else:
        keyboard = mouse = DryOutput()

    print(f"{'live' if args.live else 'dry run'}, config {paths.config_path()}, ctrl+c to quit")

    if args.gamepad:
        return run_gamepad(cfg, estop, args.live)

    with estop, Runner(cfg, keyboard, mouse, load_samples()) as runner:
        try:
            while True:
                tick = runner.step()
                if tick:
                    output = "" if args.live else mouse
                    print(f"\r{status_line(tick, output):<120}", end = "", flush = True)
        except KeyboardInterrupt:
            print()
