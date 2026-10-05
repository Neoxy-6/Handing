from handing.recognition.classifier import UNKNOWN

class Hysteresis:
    """strict to enter a gesture, lenient to leave it"""

    def __init__(self, enter_frames: int = 4, exit_frames: int = 6, min_confidence: float = 0.8):
        self.enter_frames = enter_frames
        self.exit_frames = exit_frames
        self.min_confidence = min_confidence
        self.reset()

    def reset(self) -> None:
        self.current = UNKNOWN
        self._candidate = None
        self._streak = 0
        self._misses = 0

    def update(self, name: str, confidence: float) -> str:
        if name == self.current:
            self._candidate, self._streak, self._misses = None, 0, 0
            return self.current

        self._misses += 1

        if name != UNKNOWN and confidence >= self.min_confidence:
            self._streak = self._streak + 1 if name == self._candidate else 1
            self._candidate = name
        else:
            self._candidate, self._streak = None, 0

        if self._streak >= self.enter_frames:
            self.current = name
            self._candidate, self._streak, self._misses = None, 0, 0
        elif self._misses >= self.exit_frames:
            self.current = UNKNOWN
            self._misses = 0

        return self.current
