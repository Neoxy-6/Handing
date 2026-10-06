from handing.config.keys import split_key
from handing.config.schema import Config

def lint(cfg: Config, gesture_names: list[str]) -> list[str]:
    """problems that do not break the config but probably are not what the user wants"""
    out = []

    mouse = sorted({split_key(key)[0] for key, g in cfg.gestures.items() if g.mode in ("mouse", "joystick")})
    if len(mouse) > 1:
        out.append(f"{', '.join(mouse)} all move the mouse, they will fight over the cursor")

    if cfg.safety.lock:
        out.extend(_lock_warnings(cfg, gesture_names))

    control = cfg.detection.control_hand
    if control != "any":
        other = "left" if control == "right" else "right"
        unused = [key for key in cfg.gestures if split_key(key)[1] == other]
        if unused:
            out.append(f"control hand is {control}, so {', '.join(unused)} never run")

    return out

def _lock_warnings(cfg: Config, gesture_names: list[str]) -> list[str]:
    """only matter while safety.lock is on"""
    out = []
    unlock = cfg.safety.unlock_gesture

    if not any(g.mode == "lock" for g in cfg.gestures.values()):
        out.append("no gesture is set to lock, only the stop hotkey can stop control")

    if unlock not in gesture_names:
        out.append(f"unlock gesture '{unlock}' has no samples, control can never be unlocked")

    locking = [key for key, g in cfg.gestures.items() if split_key(key)[0] == unlock and g.mode == "lock"]
    if locking:
        out.append(f"{', '.join(locking)} locks, that hand cannot unlock with '{unlock}'")

    return out

def new_warnings(old: Config, new: Config, old_names: list[str], new_names: list[str] | None = None) -> list[str]:
    """only what a change makes worse, so known issues do not nag on every save"""
    before = set(lint(old, old_names))

    return [w for w in lint(new, old_names if new_names is None else new_names) if w not in before]
