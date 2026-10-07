from pynput.keyboard import HotKey

from handing.config.keys import SIDES, split_key
from handing.config.schema import CONTROL_HANDS, DIRECTIONS, MODES, POINTS, STYLES_FOR, Config
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
    _one_of(config.detection.control_hand, CONTROL_HANDS, "detection.control_hand")
    _one_of(config.cursor.point, POINTS, "cursor.point")

    _positive(config.recognition.k, "recognition.k")
    _positive(config.recognition.max_distance, "recognition.max_distance")
    _positive(config.stability.enter_frames, "stability.enter_frames")
    _positive(config.stability.exit_frames, "stability.exit_frames")
    _positive(config.safety.unlock_frames, "safety.unlock_frames")
    if config.safety.lock_after < 0:
        raise ValueError(f"safety.lock_after must be >= 0, got {config.safety.lock_after!r}")
    _positive(config.keyboard.repeat_ms, "keyboard.repeat_ms")
    _positive(config.cursor.joystick_speed, "cursor.joystick_speed")
    _positive(config.cursor.joystick_curve, "cursor.joystick_curve")
    _positive(config.cursor.joystick_radius, "cursor.joystick_radius")
    for axis in ("x", "y"):
        value = getattr(config.cursor, f"joystick_center_{axis}")
        if not 0 <= value <= 1:
            raise ValueError(f"cursor.joystick_center_{axis} must be in [0, 1], got {value!r}")
    if not 0 <= config.cursor.joystick_deadzone < 1:
        raise ValueError(f"cursor.joystick_deadzone must be in [0, 1), got {config.cursor.joystick_deadzone!r}")

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

    unlock = config.gestures.get(config.safety.unlock_gesture)
    if config.safety.lock and unlock and unlock.mode == "lock":
        raise ValueError(f"safety.unlock_gesture '{config.safety.unlock_gesture}' is set to lock mode, it could never unlock")

    for name, g in config.gestures.items():
        where = f"gestures.{name}"
        if "@" in name and split_key(name)[1] not in SIDES:
            raise ValueError(f"{where}: the part after @ must be left or right")

        _one_of(g.mode, MODES, f"{where}.mode")
        if g.mode in STYLES_FOR:
            _one_of(g.style, STYLES_FOR[g.mode], f"{where}.style")

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
