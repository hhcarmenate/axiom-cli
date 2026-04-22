from __future__ import annotations

import os
from pathlib import Path

import yaml

_CONFIG_DIR = Path.home() / ".axiom"
_CONFIG_FILE = _CONFIG_DIR / "config.yaml"

_DEFAULTS: dict = {
    "ecosystem_root": str(Path.home() / "AI-Ecosystem"),
}


def load() -> dict:
    if not _CONFIG_FILE.exists():
        return dict(_DEFAULTS)
    with _CONFIG_FILE.open() as f:
        data = yaml.safe_load(f) or {}
    return {**_DEFAULTS, **data}


def save(data: dict) -> None:
    _CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with _CONFIG_FILE.open("w") as f:
        yaml.safe_dump(data, f)


def ensure_created() -> bool:
    """Write config file with defaults if it does not exist. Returns True if newly created."""
    if _CONFIG_FILE.exists():
        return False
    save(dict(_DEFAULTS))
    return True


def ecosystem_root() -> Path:
    cfg = load()
    root = os.path.expanduser(cfg.get("ecosystem_root", _DEFAULTS["ecosystem_root"]))
    return Path(root)


def set_ecosystem_root(path: Path) -> None:
    cfg = load()
    cfg["ecosystem_root"] = str(path)
    save(cfg)
