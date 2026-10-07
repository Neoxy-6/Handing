import os
from pathlib import Path

APP_NAME = "Handing"

def _root() -> Path:
    """folder that holds assets/: the repo when run from source, the exe folder when built with nuitka"""
    here = Path(__file__).resolve()  # src/handing/core/paths.py, or dist/Handing/handing/core/paths.py when compiled

    return here.parents[2] if "__compiled__" in globals() else here.parents[3]

ROOT = _root()

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
