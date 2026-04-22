import subprocess
from pathlib import Path
from typing import Optional

import typer

from axiom_cli.core import config, git, skills as skills_core
from axiom_cli.ui.console import console, fail, header, info, ok, warn


def _resolve_skills(stack: Optional[str]) -> Optional[str]:
    if not stack:
        return None
    requested = [s.strip() for s in stack.split(",") if s.strip()]
    valid, unknown = skills_core.validate(requested)
    if unknown:
        warn(f"Unknown skill(s) ignored: {', '.join(unknown)}")
        available = skills_core.available()
        if available:
            console.print(f"  [muted]Available: {', '.join(available)}[/muted]")
    if not valid:
        fail("No valid skills remain after filtering. Pass --stack with valid skill names.")
        raise typer.Exit(1)
    return ",".join(valid)


def command(
    project_name: str = typer.Argument(..., help="Name of the new project directory"),
    stack: Optional[str] = typer.Option(
        None, "--stack", help="Comma-separated skills, e.g. react,tailwindcss,postgresql"
    ),
) -> None:
    """Create a new project bootstrapped with the axiom ecosystem."""
    header("axiom new")

    config.ensure_created()

    project_dir = Path.cwd() / project_name

    if project_dir.exists():
        fail(f"Directory already exists: {project_dir}")
        info("Use [cmd]axiom install[/cmd] inside an existing project instead.")
        raise typer.Exit(1)

    cleaned_stack = _resolve_skills(stack)

    info(f"Creating {project_dir}…")
    try:
        project_dir.mkdir(parents=True)
    except OSError as exc:
        fail(f"Could not create directory: {exc}")
        raise typer.Exit(1)

    info("Initialising git repository…")
    try:
        git.init(project_dir)
        ok("Git repository initialised.")
    except subprocess.CalledProcessError as exc:
        warn(f"git init failed: {exc}. Continuing without git.")

    eco = config.ecosystem_root()
    install_sh = eco / "axiom-team" / "install.sh"

    if not install_sh.is_file():
        fail(f"install.sh not found at {install_sh}. Run axiom doctor for help.")
        raise typer.Exit(1)

    cmd = ["bash", str(install_sh), "--project-dir", str(project_dir)]
    if cleaned_stack:
        cmd += ["--skills", cleaned_stack]

    info("Installing axiom-team skills…")
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as exc:
        fail(f"install.sh failed (exit {exc.returncode}).")
        raise typer.Exit(1)

    console.print()
    ok(f"Project ready at [bold]{project_dir}[/bold]")
    info(f"Next step:  cd {project_name}  then start your agent.")
