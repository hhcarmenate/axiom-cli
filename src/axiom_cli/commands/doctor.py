from pathlib import Path

import typer

from axiom_cli.core import agents, config, docker
from axiom_cli.core.repos import REPOS
from axiom_cli.ui.console import console, fail, header, info, ok, warn

_DOCKER_INSTALL_URL = "https://docs.docker.com/engine/install/"

_MCP_INSTRUCTIONS = {
    "claude": (
        "Add to ~/.claude/settings.json under mcpServers:\n"
        '  "continuum": {\n'
        '    "command": "uv",\n'
        '    "args": ["run", "--directory", "~/AI-Ecosystem/continuum", "continuum"]\n'
        "  }"
    ),
    "codex": (
        "Add to ~/.codex/config.yaml:\n"
        "  mcp_servers:\n"
        "    continuum:\n"
        "      command: uv run --directory ~/AI-Ecosystem/continuum continuum"
    ),
    "cursor": (
        "Open Cursor → Settings → MCP → Add server:\n"
        "  Name: continuum\n"
        "  Command: uv run --directory ~/AI-Ecosystem/continuum continuum"
    ),
}


def command() -> None:
    """Diagnose issues and print fix instructions."""
    header("axiom doctor")

    issues: int = 0
    eco = config.ecosystem_root()

    # ── Docker ────────────────────────────────────────────────────────────────
    console.print("\n[bold]Docker[/bold]")
    if not docker.is_installed():
        issues += 1
        fail("Docker is not installed.")
        console.print(f"  [muted]→ Install it: {_DOCKER_INSTALL_URL}[/muted]")
    elif not docker.is_running():
        issues += 1
        fail("Docker is installed but the daemon is not running.")
        console.print("  [muted]→ Start Docker Desktop or run: sudo systemctl start docker[/muted]")
    else:
        ok("Docker is installed and running.")

    # ── Ecosystem repos ───────────────────────────────────────────────────────
    console.print("\n[bold]Ecosystem repos[/bold]")
    for repo, url in REPOS.items():
        path = eco / repo
        if path.is_dir():
            ok(f"{repo} found at {path}")
        else:
            issues += 1
            fail(f"{repo} not found at {path}")
            console.print(f"  [muted]→ git clone {url} {path}[/muted]")

    # ── Continuum containers ──────────────────────────────────────────────────
    console.print("\n[bold]Continuum containers[/bold]")
    pg_healthy = docker.container_healthy("memory-ai-postgres-1")
    redis_healthy = docker.container_healthy("memory-ai-redis-1")

    if pg_healthy:
        ok("Postgres container is healthy.")
    else:
        issues += 1
        fail("Postgres container is not healthy.")
        console.print(f"  [muted]→ Run: docker compose up -d  (in {eco / 'continuum'})[/muted]")
        console.print("  [muted]   or simply: axiom init[/muted]")

    if redis_healthy:
        ok("Redis container is healthy.")
    else:
        issues += 1
        fail("Redis container is not healthy.")
        console.print(f"  [muted]→ Run: docker compose up -d  (in {eco / 'continuum'})[/muted]")
        console.print("  [muted]   or simply: axiom init[/muted]")

    # ── MCP configuration ─────────────────────────────────────────────────────
    console.print("\n[bold]AI agent MCP configuration[/bold]")
    detected = agents.detect()
    installed_agents = [a for a in detected if a.installed]

    if not installed_agents:
        warn("No AI agents detected (claude, codex, cursor).")
    else:
        for agent in installed_agents:
            ok(f"{agent.name} is installed.")
            instructions = _MCP_INSTRUCTIONS.get(agent.name)
            if instructions:
                info(f"Configure continuum MCP for {agent.name}:")
                for line in instructions.splitlines():
                    console.print(f"    [muted]{line}[/muted]")

    # ── Summary ───────────────────────────────────────────────────────────────
    console.print()
    if issues == 0:
        ok("Everything looks good! Run [cmd]axiom status[/cmd] for a quick health check.")
    else:
        warn(f"{issues} issue(s) found. Follow the instructions above to fix them.")
