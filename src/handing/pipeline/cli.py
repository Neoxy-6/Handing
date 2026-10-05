import argparse

from handing.config import loader
from handing.core import paths
from handing.output.dpi import enable_dpi_awareness
from handing.output.dry import DryOutput
from handing.output.estop import EmergencyStop
from handing.output.keyboard import Keyboard
from handing.output.mouse import Mouse
from handing.pipeline.runner import Runner
from handing.recognition.samples import SampleSet

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(prog = "handing", description = "gesture control in the terminal, dry run by default")
    p.add_argument("--live", action = "store_true", help = "really control the pc, ctrl+alt+q toggles stop")

    return p.parse_args()

def status_line(tick, output) -> str:
    pred = tick.prediction
    raw = f"{pred.name:8} {pred.confidence:.2f} {pred.distance:4.2f}" if pred else f"{'-':8} {'':4} {'':4}"
    state = f"{tick.status.state.value:8} {tick.status.gesture or '':8}"

    return f"{state} | raw {raw} | {output}"

def main() -> None:
    args = parse_args()
    enable_dpi_awareness()
    cfg = loader.load()

    estop = EmergencyStop(cfg.safety.estop_hotkey, on_change = lambda s: print("\nSTOPPED" if s else "\nrunning"))
    if args.live:
        keyboard, mouse = Keyboard(estop), Mouse(estop)
    else:
        keyboard = mouse = DryOutput()

    print(f"{'live' if args.live else 'dry run'}, config {paths.config_path()}, ctrl+c to quit")

    with estop, Runner(cfg, keyboard, mouse, SampleSet.load(paths.default_gestures())) as runner:
        try:
            while True:
                tick = runner.step()
                if tick:
                    output = "" if args.live else mouse
                    print(f"\r{status_line(tick, output):<120}", end = "", flush = True)
        except KeyboardInterrupt:
            print()
