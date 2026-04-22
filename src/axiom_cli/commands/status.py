import subprocess
from pathlib import Path

import typer

from axiom_cli.core import config, docker
from axiom_cli.ui.console import console, header, info, ok, warn

_SKIPPED = "[muted]–  skipped (Docker not running)[/muted]"


def _row(label: str, passing: bool, note: str = "") -> None:
    mark = "[ok]✅[/ok]" if passing else "[fail]❌[/fail]"
    suffix = f"  [muted]{note}[/muted]" if note else ""
    console.print(f"  {mark}  {label}{suffix}")


def _skipped_row(label: str) -> None:
    console.print(f"  {_SKIPPED}  {label}")


def command() -> None:
    """Health check for the axiom ecosystem."""
    header("axiom status")

    eco = config.ecosystem_root()

    docker_installed = docker.is_installed()
    docker_ok = docker_installed and docker.is_running()
    _row("Docker installed", docker_installed)
    _row("Docker daemon running", docker_ok)

    if docker_ok:
        pg_healthy = docker.container_healthy("memory-ai-postgres-1")
        redis_healthy = docker.container_healthy("memory-ai-redis-1")
        _row("Continuum postgres healthy", pg_healthy, "memory-ai-postgres-1")
        _row("Continuum redis healthy", redis_healthy, "memory-ai-redis-1")
    else:
        pg_healthy = redis_healthy = False
        _skipped_row("Continuum postgres healthy")
        _skipped_row("Continuum redis healthy")

    for repo in ("continuum", "axiom-team", "axiom-skills"):
        found = (eco / repo).is_dir()
        _row(f"Ecosystem repo: {repo}", found, str(eco / repo))

    continuum_dir = eco / "continuum"
    if continuum_dir.is_dir():
        try:
            result = subprocess.run(
                ["uv", "run", "continuum", "--help"],
                cwd=continuum_dir,
                capture_output=True,
                timeout=15,
            )
            mcp_ok = result.returncode == 0
        except Exception:
            mcp_ok = False
    else:
        mcp_ok = False
    _row("Continuum MCP server starts", mcp_ok)

    axiom_installed = Path(".axiom").is_dir()
    _row("Current dir has .axiom/ installed", axiom_installed, str(Path.cwd()))

    console.print()
    if not docker_ok:
        warn("Docker is not running. Start it before using axiom.")
    if docker_ok and (not pg_healthy or not redis_healthy):
        warn("Continuum containers are not healthy. Run [cmd]axiom init[/cmd] to start them.")
    if axiom_installed:
        ok("Project is ready.")
    else:
        info("No .axiom/ found here. Run [cmd]axiom new <name>[/cmd] or [cmd]axiom install[/cmd].")
