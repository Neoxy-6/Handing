from collections import Counter, deque

class MajorityVote:
    def __init__(self, window: int = 7):
        self._names: deque[str] = deque(maxlen = window)

    def update(self, name: str) -> str:
        """return the most common name in the window, ties go to the older one"""
        self._names.append(name)

        return Counter(self._names).most_common(1)[0][0]

    def reset(self) -> None:
        self._names.clear()
