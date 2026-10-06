from handing.config.schema import Config

def lint(cfg: Config, gesture_names: list[str]) -> list[str]:
    """problems that do not break the config but probably are not what the user wants"""
    out = []

    mouse = [name for name, g in cfg.gestures.items() if g.mode == "mouse"]
    if len(mouse) > 1:
        out.append(f"{', '.join(mouse)} all move the mouse, they will fight over the cursor")

    if not any(g.mode == "lock" for g in cfg.gestures.values()):
        out.append("no gesture is set to lock, only the stop hotkey can stop control")

    if cfg.safety.unlock_gesture not in gesture_names:
        out.append(f"unlock gesture '{cfg.safety.unlock_gesture}' has no samples, control can never be unlocked")

    return out
