from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]

def model_path(name: str = "hand_landmarker.task") -> Path:
    return ROOT / "assets" / "models" / name