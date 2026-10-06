from handing.config.keys import split_key
from handing.config.schema import Config

def lint(cfg: Config, gesture_names: list[str]) -> list[str]:
    """problems that do not break the config but probably are not what the user wants"""
    out = []

    mouse = sorted({split_key(key)[0] for key, g in cfg.gestures.items() if g.mode == "mouse"})
    if len(mouse) > 1:
        out.append(f"{', '.join(mouse)} all move the mouse, they will fight over the cursor")

    if not any(g.mode == "lock" for g in cfg.gestures.values()):
        out.append("no gesture is set to lock, only the stop hotkey can stop control")

    if cfg.safety.unlock_gesture not in gesture_names:
        out.append(f"unlock gesture '{cfg.safety.unlock_gesture}' has no samples, control can never be unlocked")

    control = cfg.detection.control_hand
    if control != "any":
        other = "left" if control == "right" else "right"
        unused = [key for key in cfg.gestures if split_key(key)[1] == other]
        if unused:
            out.append(f"control hand is {control}, so {', '.join(unused)} never run")

    unlock = [key for key, g in cfg.gestures.items() if split_key(key)[0] == cfg.safety.unlock_gesture and g.mode == "lock"]
    if unlock:
        out.append(f"{', '.join(unlock)} locks, that hand cannot unlock with '{cfg.safety.unlock_gesture}'")

    return out
