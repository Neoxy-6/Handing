import ctypes
from dataclasses import dataclass

SM_XVIRTUALSCREEN, SM_YVIRTUALSCREEN, SM_CXVIRTUALSCREEN, SM_CYVIRTUALSCREEN = 76, 77, 78, 79

@dataclass(frozen = True)
class Rect:
    left: int
    top: int
    width: int
    height: int

def virtual_screen() -> Rect:
    """bounding box of all monitors, left/top can be negative"""
    metric = ctypes.windll.user32.GetSystemMetrics

    return Rect(metric(SM_XVIRTUALSCREEN), metric(SM_YVIRTUALSCREEN), metric(SM_CXVIRTUALSCREEN), metric(SM_CYVIRTUALSCREEN))
