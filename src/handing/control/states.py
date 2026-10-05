from dataclasses import dataclass
from enum import Enum

class State(Enum):
    STANDBY = "standby"  # no hand
    LOCKED = "locked"
    IDLE = "idle"
    ACTIVE = "active"  # a gesture mode is running

@dataclass(frozen = True)
class Status:
    state: State
    gesture: str | None = None  # the running gesture when ACTIVE
    changed: bool = False  # state or gesture differs from the last frame
