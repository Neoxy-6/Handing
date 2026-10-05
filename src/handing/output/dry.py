class DryOutput:
    """stands in for both Keyboard and Mouse, remembers what would have happened"""

    blocked = False

    def __init__(self):
        self.x, self.y, self.wheel = 0.0, 0.0, 0
        self.last = ""

    def move_by(self, dx: float, dy: float) -> None:
        self.x += dx
        self.y += dy

    def scroll(self, dx: int, dy: int) -> None:
        self.wheel += dy

    def __getattr__(self, name: str):
        return lambda *args: setattr(self, "last", f"{name} {' '.join(map(str, args))}")

    def __str__(self) -> str:
        return f"cursor ({self.x:6.0f}, {self.y:6.0f})  wheel {self.wheel:4}  last: {self.last}"
