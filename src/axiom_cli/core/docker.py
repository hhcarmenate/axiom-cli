from __future__ import annotations

import subprocess
from pathlib import Path


def is_installed() -> bool:
    try:
        subprocess.run(["docker", "--version"], capture_output=True, check=True)
        return True
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False


def is_running() -> bool:
    try:
        result = subprocess.run(
            ["docker", "info"], capture_output=True, check=True
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False


def compose_up(project_dir: Path, detach: bool = True) -> subprocess.CompletedProcess:
    cmd = ["docker", "compose", "up"]
    if detach:
        cmd.append("-d")
    return subprocess.run(cmd, cwd=project_dir, check=True)


def container_healthy(container_name: str) -> bool:
    try:
        result = subprocess.run(
            ["docker", "inspect", "--format", "{{.State.Health.Status}}", container_name],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip() == "healthy"
    except subprocess.CalledProcessError:
        return False


def container_running(container_name: str) -> bool:
    try:
        result = subprocess.run(
            ["docker", "inspect", "--format", "{{.State.Running}}", container_name],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip() == "true"
    except subprocess.CalledProcessError:
        return False
