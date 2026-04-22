import subprocess
from pathlib import Path
from typing import Optional

import typer

from axiom_cli.core import config, skills as skills_core
from axiom_cli.ui.console import console, fail, header, info, ok, warn


def _resolve_skills(skills: Optional[str]) -> Optional[str]:
    if not skills:
        return None
    requested = [s.strip() for s in skills.split(",") if s.strip()]
    valid, unknown = skills_core.validate(requested)
    if unknown:
        warn(f"Unknown skill(s) ignored: {', '.join(unknown)}")
        available = skills_core.available()
        if available:
            console.print(f"  [muted]Available: {', '.join(available)}[/muted]")
    if not valid:
        fail("No valid skills remain after filtering.")
        raise typer.Exit(1)
    return ",".join(valid)


def command(
    skills: Optional[str] = typer.Option(
        None, "--skills", help="Comma-separated skills to install"
    ),
    force: bool = typer.Option(False, "--force", help="Overwrite existing files"),
) -> None:
    """Install axiom into an existing project (run from inside the project)."""
    header("axiom install")

    config.ensure_created()

    cleaned_skills = _resolve_skills(skills)
    project_dir = Path.cwd()

    eco = config.ecosystem_root()
    install_sh = eco / "axiom-team" / "install.sh"

    if not install_sh.is_file():
        fail(f"install.sh not found at {install_sh}. Run axiom doctor for help.")
        raise typer.Exit(1)

    cmd = ["bash", str(install_sh), "--project-dir", str(project_dir)]
    if cleaned_skills:
        cmd += ["--skills", cleaned_skills]
    if force:
        cmd.append("--force")

    info(f"Installing axiom-team skills into {project_dir}…")
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as exc:
        fail(f"install.sh failed (exit {exc.returncode}).")
        raise typer.Exit(1)

    ok("axiom install complete.")
