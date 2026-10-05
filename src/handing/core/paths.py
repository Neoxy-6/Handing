from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]

def model_path(name: str = "hand_landmarker.task") -> Path:
    return ROOT / "assets" / "models" / name

def recordings_dir() -> Path:
    path = ROOT / "recordings"
    path.mkdir(exist_ok = True)

    return path

def default_gestures() -> Path:
    return ROOT / "assets" / "gestures" / "default.npz"
