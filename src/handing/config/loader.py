from dataclasses import asdict, fields
from pathlib import Path

import yaml

from handing.config.schema import Config, GestureConfig
from handing.config.validate import validate
from handing.core import paths

def _section(cls, raw: dict | None, where: str):
    """build a dataclass from a dict, missing keys keep defaults, unknown keys are errors"""
    raw = raw or {}
    if cls is GestureConfig and raw.get("mode") == "joystick":
        raw = {**raw, "mode": "mouse", "style": "joystick"}  # joystick used to be its own mode
    known = {f.name for f in fields(cls)}
    unknown = set(raw) - known

    if unknown:
        raise ValueError(f"unknown key(s) in {where}: {', '.join(sorted(unknown))}")

    for f in fields(cls):
        if f.name in raw and isinstance(f.type, type) and not _fits(raw[f.name], f.type):
            raise ValueError(f"{where}.{f.name} must be {f.type.__name__}, got {raw[f.name]!r}")

    return cls(**raw)

def _fits(value, kind: type) -> bool:
    if kind is float:
        return isinstance(value, (int, float)) and not isinstance(value, bool)

    return isinstance(value, kind)

def from_dict(raw: dict) -> Config:
    config = Config()

    for f in fields(Config):
        if f.name not in raw:
            continue

        if f.name == "macros":
            config.macros = dict(raw["macros"] or {})
        elif f.name == "gestures":
            config.gestures = {
                str(name): _section(GestureConfig, g, f"gestures.{name}")
                for name, g in (raw["gestures"] or {}).items()
            }
        else:
            setattr(config, f.name, _section(f.type, raw[f.name], f.name))

    unknown = set(raw) - {f.name for f in fields(Config)}
    if unknown:
        raise ValueError(f"unknown section(s): {', '.join(sorted(unknown))}")

    return config

def to_dict(config: Config) -> dict:
    data = asdict(config)
    defaults = {f.name: f.default for f in fields(GestureConfig)}
    data["gestures"] = {
        name: {k: v for k, v in g.items() if k == "mode" or v != defaults[k]}
        for name, g in data["gestures"].items()
    }

    return data

def load(path: Path | None = None) -> Config:
    """create the file with defaults on first run"""
    path = path or paths.config_path()

    if not path.exists():
        config = Config()
        save(config, path)
        return config

    raw = yaml.safe_load(path.read_text(encoding = "utf-8")) or {}
    config = from_dict(raw)
    validate(config)

    return config

def save(config: Config, path: Path | None = None) -> None:
    path = path or paths.config_path()
    path.parent.mkdir(parents = True, exist_ok = True)
    text = yaml.safe_dump(to_dict(config), sort_keys = False, allow_unicode = True)

    path.write_text(text, encoding = "utf-8")
