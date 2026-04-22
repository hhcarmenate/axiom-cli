from __future__ import annotations

from pathlib import Path

from axiom_cli.core.config import ecosystem_root


def available() -> list[str]:
    """Return skill names present in axiom-skills/skills/."""
    skills_dir = ecosystem_root() / "axiom-skills" / "skills"
    if not skills_dir.is_dir():
        return []
    return sorted(
        p.name for p in skills_dir.iterdir() if p.is_dir() and not p.name.startswith(".")
    )


def validate(requested: list[str]) -> tuple[list[str], list[str]]:
    """Return (valid, unknown) given a list of requested skill names."""
    known = set(available())
    valid = [s for s in requested if s in known]
    unknown = [s for s in requested if s not in known]
    return valid, unknown
