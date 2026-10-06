from handing.config.keys import split_key
from handing.control.states import State, Status

LOCK_MODE = "lock"

class StateMachine:
    def __init__(self, modes: dict[str, str], unlock_gesture: str, unlock_frames: int = 15, relock_ms: int = 5000, use_lock: bool = True):
        """modes: config key (gesture or gesture@hand) -> mode name"""
        self.modes = modes
        self.unlock_gesture = unlock_gesture
        self.unlock_frames = unlock_frames
        self.relock_ms = relock_ms
        self.use_lock = use_lock  # False: never locked, lock gestures do nothing

        self.state = State.STANDBY
        self.gesture: str | None = None
        self._locked = use_lock  # state to resume after standby
        self._standby_since = 0
        self._unlock_streak = 0
        self._ignore: str | None = None  # gesture name held while unlocking, ignored on both hands until it changes

    def update(self, gesture: str | None, timestamp_ms: int) -> Status:
        """gesture: config key of the stable gesture, None when no hand"""
        before = (self.state, self.gesture)

        if gesture is None:
            self._to_standby(timestamp_ms)
        else:
            if self.state == State.STANDBY:
                self._resume(timestamp_ms)
            self._step(gesture)

        return Status(self.state, self.gesture, (self.state, self.gesture) != before)

    def _to_standby(self, timestamp_ms: int) -> None:
        if self.state != State.STANDBY:
            self._locked = self.state == State.LOCKED
            self._standby_since = timestamp_ms
            self._set(State.STANDBY)

    def _resume(self, timestamp_ms: int) -> None:
        if self.use_lock and (self._locked or timestamp_ms - self._standby_since > self.relock_ms):
            self._lock()
        else:
            self._set(State.IDLE)

    def _step(self, gesture: str) -> None:
        mode = self.modes.get(gesture)

        if mode == LOCK_MODE:
            if self.use_lock:
                self._lock()
            else:
                self._set(State.IDLE)
            return

        name = split_key(gesture)[0]

        if self.state == State.LOCKED:
            self._unlock_streak = self._unlock_streak + 1 if name == self.unlock_gesture else 0  # either hand unlocks
            if self._unlock_streak >= self.unlock_frames:
                self._ignore = name
                self._set(State.IDLE)
            return

        if name != self._ignore:
            self._ignore = None

        if mode is None or name == self._ignore:
            self._set(State.IDLE)
        else:
            self._set(State.ACTIVE, gesture)

    def _lock(self) -> None:
        self._unlock_streak = 0
        self._set(State.LOCKED)

    def _set(self, state: State, gesture: str | None = None) -> None:
        self.state = state
        self.gesture = gesture
