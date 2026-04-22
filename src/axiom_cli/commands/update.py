import subprocess
from pathlib import Path

import typer

from axiom_cli.core import config, git
from axiom_cli.ui.console import fail, header, info, ok, warn

_REPOS = ("continuum", "axiom-team", "axiom-skills")


def command() -> None:
    """Pull latest changes for all ecosystem repos."""
    header("axiom update")

    eco = config.ecosystem_root()
    any_failed = False

    for repo in _REPOS:
        path = eco / repo
        if not path.is_dir():
            warn(f"{repo}: not found at {path} — skipping.")
            continue
        info(f"Pulling {repo}…")
        try:
            result = git.pull(path)
            if result.stdout.strip():
                for line in result.stdout.strip().splitlines():
                    print(f"  {line}")
            ok(f"{repo} updated.")
        except subprocess.CalledProcessError as exc:
            fail(f"{repo}: git pull failed.")
            if exc.stderr:
                print(exc.stderr.strip())
            any_failed = True

    if Path(".axiom").is_dir():
        info(
            "This project has .axiom/ — consider running [cmd]axiom install --force[/cmd] "
            "to pick up the latest skills."
        )

    raise typer.Exit(1 if any_failed else 0)
