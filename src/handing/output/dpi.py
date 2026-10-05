import ctypes
import sys

PER_MONITOR_AWARE = 2

def enable_dpi_awareness() -> None:
    """call once at startup, before any window, so pixel coords match the real screen"""
    if sys.platform != "win32":
        return

    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(PER_MONITOR_AWARE)
    except (AttributeError, OSError):
        ctypes.windll.user32.SetProcessDPIAware()
