import subprocess
import time
from pathlib import Path
from typing import Optional

import typer
from rich.progress import Progress, SpinnerColumn, TextColumn

from axiom_cli.core import agents, config, docker
from axiom_cli.core.repos import REPOS
from axiom_cli.ui.console import console, fail, header, info, ok, warn


def _wait_healthy(container: str, retries: int = 24, delay: float = 2.5) -> bool:
    for _ in range(retries):
        if docker.container_healthy(container):
            return True
        time.sleep(delay)
    return False


def _check_repos(eco: Path) -> list[str]:
    """Return names of repos that are missing from the ecosystem root."""
    return [name for name in REPOS if not (eco / name).is_dir()]


def _clone_repos(missing: list[str], eco: Path) -> bool:
    """Clone each missing repo. Returns True if all succeeded."""
    all_ok = True
    for name in missing:
        url = REPOS[name]
        dest = eco / name
        info(f"Cloning {name} from {url}…")
        try:
            subprocess.run(
                ["git", "clone", url, str(dest)],
                check=True,
                capture_output=True,
                text=True,
            )
            ok(f"{name} cloned.")
        except subprocess.CalledProcessError as exc:
            fail(f"Failed to clone {name}: {exc.stderr.strip() or exc}")
            all_ok = False
    return all_ok


def command(
    ecosystem_root: Optional[Path] = typer.Option(
        None,
        "--ecosystem-root",
        help="Override path to the AI-Ecosystem directory (saved to ~/.axiom/config.yaml)",
        show_default=False,
    ),
    clone: bool = typer.Option(
        False,
        "--clone",
        help="Clone any missing ecosystem repos before continuing",
    ),
) -> None:
    """Global setup — run once per machine."""
    header("axiom init")

    # ── Config ────────────────────────────────────────────────────────────────
    if ecosystem_root is not None:
        config.set_ecosystem_root(ecosystem_root.expanduser().resolve())
        ok(f"Ecosystem root set to {config.ecosystem_root()}")
    elif config.ensure_created():
        info(f"Created ~/.axiom/config.yaml (ecosystem root: {config.ecosystem_root()})")

    eco = config.ecosystem_root()

    # ── Ecosystem repos ───────────────────────────────────────────────────────
    missing = _check_repos(eco)
    if missing:
        if not clone:
            fail("The following ecosystem repos are missing:")
            for name in missing:
                console.print(f"  [fail]✗[/fail]  {eco / name}  [muted]({REPOS[name]})[/muted]")
            console.print()
            info("Run [cmd]axiom init --clone[/cmd] to clone them automatically.")
            raise typer.Exit(1)

        eco.mkdir(parents=True, exist_ok=True)
        if not _clone_repos(missing, eco):
            fail("Some repos could not be cloned. Fix the errors above and retry.")
            raise typer.Exit(1)
    else:
        for name in REPOS:
            ok(f"Ecosystem repo found: {name}")

    # ── Docker ────────────────────────────────────────────────────────────────
    if not docker.is_installed():
        fail("Docker is not installed. Install it from https://docs.docker.com/engine/install/")
        raise typer.Exit(1)

    if not docker.is_running():
        fail("Docker daemon is not running. Start Docker and re-run axiom init.")
        raise typer.Exit(1)

    ok("Docker is installed and running.")

    # ── Start continuum ───────────────────────────────────────────────────────
    continuum_dir = eco / "continuum"
    info("Starting continuum containers…")
    try:
        docker.compose_up(continuum_dir)
    except subprocess.CalledProcessError as exc:
        fail(f"docker compose up failed: {exc}")
        raise typer.Exit(1)

    # ── Wait for health ───────────────────────────────────────────────────────
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
        console=console,
    ) as progress:
        task = progress.add_task("Waiting for postgres…", total=None)
        pg_ok = _wait_healthy("memory-ai-postgres-1")
        progress.update(task, description="Waiting for redis…")
        redis_ok = _wait_healthy("memory-ai-redis-1")

    if pg_ok:
        ok("Postgres is healthy.")
    else:
        fail("Postgres did not become healthy in time. Check: docker logs memory-ai-postgres-1")
        raise typer.Exit(1)

    if redis_ok:
        ok("Redis is healthy.")
    else:
        fail("Redis did not become healthy in time. Check: docker logs memory-ai-redis-1")
        raise typer.Exit(1)

    # ── Verify MCP server ─────────────────────────────────────────────────────
    info("Verifying continuum MCP server…")
    try:
        result = subprocess.run(
            ["uv", "run", "continuum", "--help"],
            cwd=continuum_dir,
            capture_output=True,
            timeout=20,
        )
        if result.returncode == 0:
            ok("Continuum MCP server is ready.")
        else:
            warn("continuum --help returned non-zero. Check your continuum installation.")
    except Exception as exc:
        warn(f"Could not verify continuum MCP server: {exc}")

    # ── Detect agents and print MCP setup hints ───────────────────────────────
    console.print()
    info("Detected AI agents:")
    detected = agents.detect()
    for agent in detected:
        mark = "[ok]✅[/ok]" if agent.installed else "[muted]–[/muted]"
        console.print(f"  {mark}  {agent.name}")

    installed = [a for a in detected if a.installed]
    if installed:
        console.print()
        info("Next step — configure the continuum MCP server for each agent:")
        console.print("  Run [cmd]axiom doctor[/cmd] for exact configuration commands.")
    else:
        warn("No AI agents detected. Install claude, codex, or cursor, then run axiom doctor.")

    console.print()
    ok("axiom init complete. Your ecosystem is running.")
