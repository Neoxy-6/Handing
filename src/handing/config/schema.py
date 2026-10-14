from dataclasses import dataclass, field

MODES = ("mouse", "drag", "scroll", "lock", "trigger", "action")
STYLES_FOR = {  # modes that take a style, first one is the default
    "mouse": ("joystick", "relative"),
}
STYLED = tuple(STYLES_FOR)
POINTS = ("palm", "index")
POINTED = ("mouse", "drag", "scroll", "trigger")  # modes that follow a point on the hand
CONTROL_HANDS = ("any", "left", "right")
DIRECTIONS = ("left", "right", "up", "down")
APP_MODES = ("standard", "gamepad")
PAD_BUTTONS = ("A", "B", "X", "Y", "LB", "RB", "BACK", "START", "LS", "RS", "UP", "DOWN", "LEFT", "RIGHT")
PAD_TRIGGERS = ("LT", "RT")

@dataclass
class AppConfig:
    mode: str = "standard"  # standard: mouse and keyboard, gamepad: a virtual xbox controller

@dataclass
class CameraConfig:
    index: int = 0
    width: int = 640
    idle_fps: int = 8  # frames per second while no hand is seen, 0 = never slow down
    mirrored: bool = False  # the driver already flips the frame like a mirror
    flip: bool = True  # flip the frame ourselves, so the preview reads like a mirror

    @property
    def frame_mirrored(self) -> bool:
        """whether the frame the pipeline sees is a mirror image"""
        return self.mirrored != self.flip

@dataclass
class DetectionConfig:
    hands: int = 1
    min_confidence: float = 0.5
    control_hand: str = "any"  # left / right ignores the other hand, detection then always looks for two

@dataclass
class RecognitionConfig:
    k: int = 5
    max_distance: float = 2.0
    align_rotation: bool = True  # turn poses upright before comparing, gestures that differ only by direction merge

@dataclass
class StabilityConfig:
    enter_frames: int = 4
    exit_frames: int = 6
    min_confidence: float = 0.8

@dataclass
class CursorConfig:
    min_cutoff: float = 0.5
    beta: float = 0.015
    joystick_deadzone: float = 0.1  # share of the stick radius that does nothing
    joystick_speed: float = 600.0  # screen px per second at full push
    joystick_curve: float = 1.5  # 1 = linear, higher = finer near the center
    joystick_center_x: float = 0.5  # as seen in the preview, 0 = left edge
    joystick_center_y: float = 0.3  # 0 = top edge
    joystick_radius: float = 0.2  # share of the frame height for full push

@dataclass
class SafetyConfig:
    estop_hotkey: str = "<ctrl>+<alt>+q"
    lock: bool = False  # start locked, need the unlock gesture, lock again after the hand leaves
    lock_after: float = 5.0  # seconds without a hand before locking again
    unlock_gesture: str = "point"
    unlock_frames: int = 15

@dataclass
class MouseConfig:
    sensitivity: float = 1.5
    deadzone: float = 0.2  # camera px per frame, after smoothing

@dataclass
class KeyboardConfig:
    repeat_ms: int = 300

@dataclass
class UiConfig:
    overlay: bool = True  # status pill while the main window is hidden

@dataclass
class GestureConfig:
    mode: str
    style: str = "relative"  # mouse: relative or joystick, see STYLES_FOR
    point: str = "palm"  # part of the hand the mode follows, see POINTED
    sensitivity: float = 1.0  # scroll
    threshold: float = 0.15  # trigger, fraction of frame width
    left: str | None = None
    right: str | None = None
    up: str | None = None
    down: str | None = None
    action: str | None = None  # action mode
    repeat: bool = False  # action mode, re-run while held

@dataclass
class PadBinding:
    button: str  # see PAD_BUTTONS and PAD_TRIGGERS
    repeat: bool = False  # press and release every keyboard.repeat_ms while the gesture is held

def default_bindings() -> dict[str, PadBinding]:
    return {
        "fist@left": PadBinding("LT"),
        "peace@left": PadBinding("LB"),
        "fist@right": PadBinding("RT"),
        "point@right": PadBinding("A"),
        "peace@right": PadBinding("B"),
    }

@dataclass
class GamepadConfig:
    sticks: bool = True  # while a hand is in view its palm drives the stick on its side
    left_center_x: float = 0.25  # stick centers, 0 = the user's left edge whether or not the frame is flipped
    right_center_x: float = 0.75
    center_y: float = 0.5  # 0 = top edge
    radius: float = 0.2  # share of the frame height for full push
    deadzone: float = 0.25  # share of the radius, hands drift more than thumbs
    curve: float = 1.0  # 1 = linear, higher = finer near the center
    bindings: dict[str, PadBinding] = field(default_factory = default_bindings)  # gesture key -> button, held while the gesture is

def default_gestures() -> dict[str, GestureConfig]:
    return {
        "point": GestureConfig("mouse", style = "joystick", point = "index"),
        "fist": GestureConfig("scroll"),
        "peace": GestureConfig("action", action = "click:left"),
    }

@dataclass
class Config:
    app: AppConfig = field(default_factory = AppConfig)
    camera: CameraConfig = field(default_factory = CameraConfig)
    detection: DetectionConfig = field(default_factory = DetectionConfig)
    recognition: RecognitionConfig = field(default_factory = RecognitionConfig)
    stability: StabilityConfig = field(default_factory = StabilityConfig)
    cursor: CursorConfig = field(default_factory = CursorConfig)
    safety: SafetyConfig = field(default_factory = SafetyConfig)
    mouse: MouseConfig = field(default_factory = MouseConfig)
    keyboard: KeyboardConfig = field(default_factory = KeyboardConfig)
    ui: UiConfig = field(default_factory = UiConfig)
    macros: dict[str, list] = field(default_factory = dict)  # raw steps, see output/macro.py
    gestures: dict[str, GestureConfig] = field(default_factory = default_gestures)
    gamepad: GamepadConfig = field(default_factory = GamepadConfig)
