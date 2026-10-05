from handing.control.states import State, Status

LOCK_MODE = "lock"

class StateMachine:
    def __init__(self, modes: dict[str, str], unlock_gesture: str, unlock_frames: int = 15, relock_ms: int = 5000):
        """modes: gesture name -> mode name from config"""
        self.modes = modes
        self.unlock_gesture = unlock_gesture
        self.unlock_frames = unlock_frames
        self.relock_ms = relock_ms

        self.state = State.STANDBY
        self.gesture: str | None = None
        self._locked = True  # state to resume after standby
        self._standby_since = 0
        self._unlock_streak = 0
        self._ignore: str | None = None  # gesture held while unlocking, ignored until it changes

    def update(self, gesture: str | None, timestamp_ms: int) -> Status:
        """gesture: stable name after filtering, None when no hand"""
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
        if self._locked or timestamp_ms - self._standby_since > self.relock_ms:
            self._lock()
        else:
            self._set(State.IDLE)

    def _step(self, gesture: str) -> None:
        mode = self.modes.get(gesture)

        if mode == LOCK_MODE:
            self._lock()
            return

        if self.state == State.LOCKED:
            self._unlock_streak = self._unlock_streak + 1 if gesture == self.unlock_gesture else 0
            if self._unlock_streak >= self.unlock_frames:
                self._ignore = gesture
                self._set(State.IDLE)
            return

        if gesture != self._ignore:
            self._ignore = None

        if mode is None or gesture == self._ignore:
            self._set(State.IDLE)
        else:
            self._set(State.ACTIVE, gesture)

    def _lock(self) -> None:
        self._unlock_streak = 0
        self._set(State.LOCKED)

    def _set(self, state: State, gesture: str | None = None) -> None:
        self.state = state
        self.gesture = gesture
