from __future__ import annotations

import subprocess
from pathlib import Path


def is_installed() -> bool:
    try:
        subprocess.run(["git", "--version"], capture_output=True, check=True)
        return True
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False


def init(directory: Path) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "init"], cwd=directory, check=True, capture_output=True)


def pull(directory: Path) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "pull"], cwd=directory, check=True, text=True)
