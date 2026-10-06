import numpy as np

from handing.config.schema import DIRECTIONS, Config
from handing.control.modes.action import ActionMode
from handing.control.modes.base import Mode
from handing.control.modes.drag import DragMode
from handing.control.modes.joystick import JoystickMode
from handing.control.modes.mouse import MouseMode
from handing.control.modes.scroll import ScrollMode
from handing.control.modes.trigger import TriggerMode
from handing.filtering.one_euro import OneEuro
from handing.output.macro import ActionRunner
from handing.output.mouse import Mouse

def stick_area(cfg: Config) -> tuple[np.ndarray, float]:
    """center as seen in the preview and full-push radius, camera px, frames are 4:3"""
    width = cfg.camera.width
    height = width * 3 / 4
    c = cfg.cursor

    return np.array([c.joystick_center_x * width, c.joystick_center_y * height]), c.joystick_radius * height

def control_center(cfg: Config, preview_center: np.ndarray) -> np.ndarray:
    """control points have x toward the user's right, the raw preview is flipped unless mirrored"""
    center = preview_center.copy()
    if not cfg.camera.mirrored:
        center[0] = cfg.camera.width - center[0]

    return center

def build_modes(cfg: Config, mouse: Mouse, runner: ActionRunner, screen_width: int) -> dict[str, Mode]:
    """gesture name -> mode object, lock gestures are handled by the state machine"""
    modes: dict[str, Mode] = {}

    c = cfg.cursor

    def smoother() -> OneEuro:
        return OneEuro(cfg.cursor.min_cutoff, cfg.cursor.beta)

    for name, g in cfg.gestures.items():
        if g.mode in ("mouse", "drag"):
            gain = cfg.mouse.sensitivity * screen_width / cfg.camera.width
            kind = DragMode if g.mode == "drag" else MouseMode
            modes[name] = kind(mouse, gain, cfg.mouse.deadzone, smoother())
        elif g.mode == "joystick":
            center, radius = stick_area(cfg)
            modes[name] = JoystickMode(mouse, control_center(cfg, center), radius, c.joystick_deadzone, c.joystick_speed, c.joystick_curve, smoother())
        elif g.mode == "scroll":
            modes[name] = ScrollMode(mouse, g.sensitivity, smoother())
        elif g.mode == "trigger":
            actions = {d: getattr(g, d) for d in DIRECTIONS}
            modes[name] = TriggerMode(runner, actions, g.threshold * cfg.camera.width)
        elif g.mode == "action":
            modes[name] = ActionMode(runner, g.action, g.repeat)

    return modes
