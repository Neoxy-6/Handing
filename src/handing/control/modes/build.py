from handing.config.schema import DIRECTIONS, Config
from handing.control.modes.action import ActionMode
from handing.control.modes.base import Mode
from handing.control.modes.mouse import MouseMode
from handing.control.modes.scroll import ScrollMode
from handing.control.modes.trigger import TriggerMode
from handing.filtering.one_euro import OneEuro
from handing.output.macro import ActionRunner
from handing.output.mouse import Mouse

def build_modes(cfg: Config, mouse: Mouse, runner: ActionRunner, screen_width: int) -> dict[str, Mode]:
    """gesture name -> mode object, lock gestures are handled by the state machine"""
    modes: dict[str, Mode] = {}

    def smoother() -> OneEuro:
        return OneEuro(cfg.cursor.min_cutoff, cfg.cursor.beta)

    for name, g in cfg.gestures.items():
        if g.mode == "mouse":
            gain = cfg.mouse.sensitivity * screen_width / cfg.camera.width
            modes[name] = MouseMode(mouse, gain, cfg.mouse.deadzone, smoother())
        elif g.mode == "scroll":
            modes[name] = ScrollMode(mouse, g.sensitivity, smoother())
        elif g.mode == "trigger":
            actions = {d: getattr(g, d) for d in DIRECTIONS}
            modes[name] = TriggerMode(runner, actions, g.threshold * cfg.camera.width)
        elif g.mode == "action":
            modes[name] = ActionMode(runner, g.action, g.repeat)

    return modes
