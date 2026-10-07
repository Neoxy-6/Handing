from dataclasses import dataclass, field

MODES = ("mouse", "drag", "scroll", "lock", "trigger", "action")
STYLES_FOR = {  # modes that take a style, first one is the default
    "mouse": ("relative", "joystick"),
    "drag": ("relative", "joystick"),
}
STYLED = tuple(STYLES_FOR)
MOUSE_MODES = ("relative", "absolute", "joystick")
POINTS = ("palm", "index")
CONTROL_HANDS = ("any", "left", "right")
DIRECTIONS = ("left", "right", "up", "down")

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
    align_rotation: bool = False  # turn poses upright before comparing, gestures that differ only by direction merge

@dataclass
class StabilityConfig:
    enter_frames: int = 4
    exit_frames: int = 6
    min_confidence: float = 0.8

@dataclass
class CursorConfig:
    point: str = "palm"
    min_cutoff: float = 0.5
    beta: float = 0.015
    joystick_deadzone: float = 0.15  # share of the stick radius that does nothing
    joystick_speed: float = 600.0  # screen px per second at full push
    joystick_curve: float = 1.5  # 1 = linear, higher = finer near the center
    joystick_center_x: float = 0.5  # as seen in the preview, 0 = left edge
    joystick_center_y: float = 0.5  # 0 = top edge
    joystick_radius: float = 0.4  # share of the frame height for full push

@dataclass
class SafetyConfig:
    estop_hotkey: str = "<ctrl>+<alt>+q"
    lock: bool = False  # start locked, need the unlock gesture, lock again after the hand leaves
    lock_after: float = 5.0  # seconds without a hand before locking again
    unlock_gesture: str = "paper"
    unlock_frames: int = 15

@dataclass
class MouseConfig:
    mode: str = "relative"
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
    style: str = "relative"  # mouse / drag: relative or joystick, see STYLES_FOR
    sensitivity: float = 1.0  # scroll
    threshold: float = 0.15  # trigger, fraction of frame width
    left: str | None = None
    right: str | None = None
    up: str | None = None
    down: str | None = None
    action: str | None = None  # action mode
    repeat: bool = False  # action mode, re-run while held

def default_gestures() -> dict[str, GestureConfig]:
    return {
        "peace": GestureConfig("drag"),
        "point": GestureConfig("mouse", style = "joystick"),
        "fist": GestureConfig("scroll"),
    }

@dataclass
class Config:
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
