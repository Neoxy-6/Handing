import os
from pathlib import Path

APP_NAME = "Handing"
ROOT = Path(__file__).resolve().parents[3]

def model_path(name: str = "hand_landmarker.task") -> Path:
    return ROOT / "assets" / "models" / name

def recordings_dir() -> Path:
    path = ROOT / "recordings"
    path.mkdir(exist_ok = True)

    return path

def app_icon() -> Path:
    return ROOT / "assets" / "icon" / "handing.ico"

def default_gestures() -> Path:
    return ROOT / "assets" / "gestures" / "default.npz"

def user_dir() -> Path:
    """%APPDATA%/Handing, created if missing"""
    path = Path(os.environ.get("APPDATA") or Path.home()) / APP_NAME
    path.mkdir(parents = True, exist_ok = True)

    return path

def config_path() -> Path:
    return user_dir() / "config.yaml"

def user_gestures() -> Path:
    """user's gesture samples, the app copies default.npz here on first run"""
    return user_dir() / "gestures.npz"
