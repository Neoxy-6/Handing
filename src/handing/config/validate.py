from pynput.keyboard import HotKey

from handing.config.schema import DIRECTIONS, MODES, MOUSE_MODES, POINTS, Config
from handing.output.macro import check_action, parse_macro

def _one_of(value, options, where: str) -> None:
    if value not in options:
        raise ValueError(f"{where} must be one of {', '.join(map(str, options))}, got {value!r}")

def _positive(value, where: str) -> None:
    if value <= 0:
        raise ValueError(f"{where} must be > 0, got {value!r}")

def validate(config: Config) -> None:
    """raise ValueError with the config path of the first problem"""
    _one_of(config.detection.hands, (1, 2), "detection.hands")
    _one_of(config.cursor.point, POINTS, "cursor.point")
    _one_of(config.mouse.mode, MOUSE_MODES, "mouse.mode")

    _positive(config.recognition.k, "recognition.k")
    _positive(config.recognition.max_distance, "recognition.max_distance")
    _positive(config.stability.enter_frames, "stability.enter_frames")
    _positive(config.stability.exit_frames, "stability.exit_frames")
    _positive(config.safety.unlock_frames, "safety.unlock_frames")
    _positive(config.keyboard.repeat_ms, "keyboard.repeat_ms")

    try:
        HotKey.parse(config.safety.estop_hotkey)
    except ValueError as e:
        raise ValueError(f"safety.estop_hotkey: bad key '{e}', write it like <ctrl>+<alt>+q") from None

    macros = {}
    for name, steps in config.macros.items():
        try:
            macros[name] = parse_macro(steps)
        except ValueError as e:
            raise ValueError(f"macros.{name}: {e}") from None

    for name, g in config.gestures.items():
        where = f"gestures.{name}"
        _one_of(g.mode, MODES, f"{where}.mode")

        if g.mode == "action" and not g.action:
            raise ValueError(f"{where}.action is required for action mode")

        if g.mode == "trigger" and not any(getattr(g, d) for d in DIRECTIONS):
            raise ValueError(f"{where} needs at least one of {', '.join(DIRECTIONS)}")

        actions = [g.action] + [getattr(g, d) for d in DIRECTIONS]
        for action in filter(None, actions):
            try:
                check_action(action, macros)
            except ValueError as e:
                raise ValueError(f"{where}: {e}") from None
