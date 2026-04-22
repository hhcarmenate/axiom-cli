from __future__ import annotations

import shutil
from dataclasses import dataclass


@dataclass
class AgentInfo:
    name: str
    binary: str
    installed: bool


_KNOWN_AGENTS = [
    ("claude", "claude"),
    ("codex", "codex"),
    ("cursor", "cursor"),
]


def detect() -> list[AgentInfo]:
    return [
        AgentInfo(name=name, binary=binary, installed=shutil.which(binary) is not None)
        for name, binary in _KNOWN_AGENTS
    ]
