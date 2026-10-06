SEP = "@"
SIDES = ("left", "right")

def make_key(name: str, hand: str = "any") -> str:
    """'point', 'left' -> 'point@left', any hand keeps the plain name"""
    return name if hand == "any" else f"{name}{SEP}{hand}"

def split_key(key: str) -> tuple[str, str]:
    """'point@left' -> ('point', 'left'), 'point' -> ('point', 'any')"""
    name, sep, hand = key.partition(SEP)
    return (name, hand) if sep else (key, "any")

def resolve(gestures: dict, name: str, handedness: str) -> str:
    """the config key that applies to this gesture on this hand, hand specific first"""
    key = make_key(name, handedness.lower())
    return key if key in gestures else name

def variants(gestures: dict, name: str) -> list[str]:
    """every config key of one gesture"""
    return [k for k in gestures if split_key(k)[0] == name]
