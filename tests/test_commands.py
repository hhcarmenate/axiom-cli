from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from axiom_cli.main import app

runner = CliRunner()


# ── CLI shape ─────────────────────────────────────────────────────────────────

def test_help():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    for cmd in ("init", "new", "install", "status", "update", "doctor"):
        assert cmd in result.output


def test_new_requires_project_name():
    result = runner.invoke(app, ["new"])
    assert result.exit_code != 0


# ── axiom status ──────────────────────────────────────────────────────────────

def test_status_runs():
    with (
        patch("axiom_cli.core.docker.is_installed", return_value=True),
        patch("axiom_cli.core.docker.is_running", return_value=True),
        patch("axiom_cli.core.docker.container_healthy", return_value=True),
        patch("axiom_cli.commands.status.subprocess.run", return_value=MagicMock(returncode=0)),
    ):
        result = runner.invoke(app, ["status"])
    assert result.exit_code == 0


def test_status_docker_not_running_skips_containers():
    with (
        patch("axiom_cli.core.docker.is_installed", return_value=True),
        patch("axiom_cli.core.docker.is_running", return_value=False),
        patch("axiom_cli.core.docker.container_healthy") as mock_healthy,
        patch("axiom_cli.commands.status.subprocess.run", return_value=MagicMock(returncode=1)),
    ):
        result = runner.invoke(app, ["status"])
    assert result.exit_code == 0
    assert "Docker" in result.output
    # container_healthy must never be called when Docker isn't running
    mock_healthy.assert_not_called()


# ── axiom doctor ──────────────────────────────────────────────────────────────

def test_doctor_runs():
    with (
        patch("axiom_cli.core.docker.is_installed", return_value=True),
        patch("axiom_cli.core.docker.is_running", return_value=True),
        patch("axiom_cli.core.docker.container_healthy", return_value=True),
    ):
        result = runner.invoke(app, ["doctor"])
    assert result.exit_code == 0


def test_doctor_missing_docker():
    with (
        patch("axiom_cli.core.docker.is_installed", return_value=False),
        patch("axiom_cli.core.docker.is_running", return_value=False),
        patch("axiom_cli.core.docker.container_healthy", return_value=False),
    ):
        result = runner.invoke(app, ["doctor"])
    assert result.exit_code == 0
    assert "Docker" in result.output


# ── axiom init ────────────────────────────────────────────────────────────────

def test_init_aborts_missing_repos(tmp_path):
    """axiom init without --clone must fail when repos are missing."""
    with patch("axiom_cli.core.config.ecosystem_root", return_value=tmp_path):
        result = runner.invoke(app, ["init"])
    assert result.exit_code != 0
    assert "missing" in result.output.lower()
    assert "--clone" in result.output


def test_init_clone_clones_missing_repos(tmp_path):
    """axiom init --clone should git-clone missing repos then continue."""
    with (
        patch("axiom_cli.core.config.ecosystem_root", return_value=tmp_path),
        patch("axiom_cli.commands.init._clone_repos", return_value=True) as mock_clone,
        patch("axiom_cli.core.docker.is_installed", return_value=False),
    ):
        result = runner.invoke(app, ["init", "--clone"])
    mock_clone.assert_called_once()
    # Stops at Docker (not installed) — repos were handled first
    assert result.exit_code != 0
    assert "Docker" in result.output


def test_init_all_repos_present_proceeds_to_docker(tmp_path):
    """When all repos exist, init should move on and check Docker."""
    for name in ("continuum", "axiom-team", "axiom-skills"):
        (tmp_path / name).mkdir()
    with (
        patch("axiom_cli.core.config.ecosystem_root", return_value=tmp_path),
        patch("axiom_cli.core.docker.is_installed", return_value=False),
    ):
        result = runner.invoke(app, ["init"])
    assert "Docker" in result.output
    assert result.exit_code != 0


def test_init_aborts_without_docker(tmp_path):
    for name in ("continuum", "axiom-team", "axiom-skills"):
        (tmp_path / name).mkdir()
    with (
        patch("axiom_cli.core.config.ecosystem_root", return_value=tmp_path),
        patch("axiom_cli.core.docker.is_installed", return_value=False),
    ):
        result = runner.invoke(app, ["init"])
    assert result.exit_code != 0
    assert "Docker" in result.output


def test_init_aborts_docker_not_running(tmp_path):
    for name in ("continuum", "axiom-team", "axiom-skills"):
        (tmp_path / name).mkdir()
    with (
        patch("axiom_cli.core.config.ecosystem_root", return_value=tmp_path),
        patch("axiom_cli.core.docker.is_installed", return_value=True),
        patch("axiom_cli.core.docker.is_running", return_value=False),
    ):
        result = runner.invoke(app, ["init"])
    assert result.exit_code != 0


def test_init_ecosystem_root_option(tmp_path):
    custom_root = tmp_path / "custom-eco"
    custom_root.mkdir()
    with (
        patch("axiom_cli.core.docker.is_installed", return_value=False),
        patch("axiom_cli.core.config.set_ecosystem_root") as mock_set,
    ):
        runner.invoke(app, ["init", "--ecosystem-root", str(custom_root)])
    mock_set.assert_called_once()


# ── axiom new ─────────────────────────────────────────────────────────────────

def test_new_aborts_if_dir_exists(tmp_path):
    existing = tmp_path / "myproject"
    existing.mkdir()
    with patch("axiom_cli.commands.new.Path.cwd", return_value=tmp_path):
        result = runner.invoke(app, ["new", "myproject"])
    assert result.exit_code != 0
    assert "already exists" in result.output


def test_new_creates_project(tmp_path):
    axiom_team_dir = tmp_path / "axiom-team"
    axiom_team_dir.mkdir(parents=True)
    install_sh = axiom_team_dir / "install.sh"
    install_sh.write_text("#!/bin/bash\n")
    install_sh.chmod(0o755)

    with (
        patch("axiom_cli.core.config.ecosystem_root", return_value=tmp_path),
        patch("axiom_cli.commands.new.Path.cwd", return_value=tmp_path / "workspace"),
        patch("axiom_cli.core.git.init"),
        patch("axiom_cli.commands.new.subprocess.run", return_value=MagicMock(returncode=0)),
    ):
        (tmp_path / "workspace").mkdir()
        result = runner.invoke(app, ["new", "cool-project"])
    assert result.exit_code == 0
    assert "Project ready" in result.output


def test_new_warns_unknown_skills(tmp_path):
    axiom_team_dir = tmp_path / "axiom-team"
    axiom_team_dir.mkdir(parents=True)
    (axiom_team_dir / "install.sh").write_text("#!/bin/bash\n")

    skills_dir = tmp_path / "axiom-skills" / "skills"
    skills_dir.mkdir(parents=True)
    (skills_dir / "react").mkdir()

    with (
        patch("axiom_cli.core.config.ecosystem_root", return_value=tmp_path),
        patch("axiom_cli.commands.new.Path.cwd", return_value=tmp_path / "ws"),
        patch("axiom_cli.core.git.init"),
        patch("axiom_cli.commands.new.subprocess.run", return_value=MagicMock(returncode=0)),
    ):
        (tmp_path / "ws").mkdir()
        result = runner.invoke(app, ["new", "proj", "--stack", "react,nonexistent"])
    assert "Unknown skill" in result.output
    assert result.exit_code == 0


def test_new_aborts_all_invalid_skills(tmp_path):
    skills_dir = tmp_path / "axiom-skills" / "skills"
    skills_dir.mkdir(parents=True)
    (skills_dir / "react").mkdir()

    with (
        patch("axiom_cli.core.config.ecosystem_root", return_value=tmp_path),
        patch("axiom_cli.commands.new.Path.cwd", return_value=tmp_path / "ws"),
    ):
        (tmp_path / "ws").mkdir()
        result = runner.invoke(app, ["new", "proj", "--stack", "notareal,alsofake"])
    assert result.exit_code != 0


# ── axiom install ─────────────────────────────────────────────────────────────

def test_install_aborts_missing_install_sh(tmp_path):
    with patch("axiom_cli.core.config.ecosystem_root", return_value=tmp_path):
        result = runner.invoke(app, ["install"])
    assert result.exit_code != 0
    assert "install.sh not found" in result.output


def test_install_with_valid_skills(tmp_path):
    axiom_team_dir = tmp_path / "axiom-team"
    axiom_team_dir.mkdir(parents=True)
    (axiom_team_dir / "install.sh").write_text("#!/bin/bash\n")

    skills_dir = tmp_path / "axiom-skills" / "skills"
    skills_dir.mkdir(parents=True)
    (skills_dir / "react").mkdir()

    with (
        patch("axiom_cli.core.config.ecosystem_root", return_value=tmp_path),
        patch("axiom_cli.commands.install.subprocess.run", return_value=MagicMock(returncode=0)),
    ):
        result = runner.invoke(app, ["install", "--skills", "react"])
    assert result.exit_code == 0
    assert "complete" in result.output


# ── axiom update ──────────────────────────────────────────────────────────────

def test_update_skips_missing_repos(tmp_path):
    with patch("axiom_cli.core.config.ecosystem_root", return_value=tmp_path):
        result = runner.invoke(app, ["update"])
    assert "skipping" in result.output


def test_update_pulls_existing_repo(tmp_path):
    (tmp_path / "continuum").mkdir()
    (tmp_path / "axiom-team").mkdir()
    (tmp_path / "axiom-skills").mkdir()
    mock_result = MagicMock(returncode=0, stdout="Already up to date.\n", stderr="")
    with (
        patch("axiom_cli.core.config.ecosystem_root", return_value=tmp_path),
        patch("axiom_cli.core.git.pull", return_value=mock_result),
    ):
        result = runner.invoke(app, ["update"])
    assert result.exit_code == 0
    assert "updated" in result.output


# ── Core: config ──────────────────────────────────────────────────────────────

def test_config_load_returns_dict():
    from axiom_cli.core.config import load
    cfg = load()
    assert isinstance(cfg, dict)
    assert "ecosystem_root" in cfg


def test_config_ensure_created(tmp_path):
    from axiom_cli.core import config as cfg_mod
    fake_config = tmp_path / "config.yaml"
    with (
        patch.object(cfg_mod, "_CONFIG_DIR", tmp_path),
        patch.object(cfg_mod, "_CONFIG_FILE", fake_config),
    ):
        created = cfg_mod.ensure_created()
        assert created is True
        assert fake_config.exists()
        created_again = cfg_mod.ensure_created()
        assert created_again is False


# ── Core: skills ─────────────────────────────────────────────────────────────

def test_skills_available(tmp_path):
    skills_dir = tmp_path / "axiom-skills" / "skills"
    skills_dir.mkdir(parents=True)
    for name in ("react", "tailwindcss", "postgresql"):
        (skills_dir / name).mkdir()

    with patch("axiom_cli.core.skills.ecosystem_root", return_value=tmp_path):
        from axiom_cli.core import skills
        result = skills.available()
    assert sorted(result) == ["postgresql", "react", "tailwindcss"]


def test_skills_validate(tmp_path):
    skills_dir = tmp_path / "axiom-skills" / "skills"
    skills_dir.mkdir(parents=True)
    (skills_dir / "react").mkdir()

    with patch("axiom_cli.core.skills.ecosystem_root", return_value=tmp_path):
        from axiom_cli.core import skills
        valid, unknown = skills.validate(["react", "bogus"])
    assert valid == ["react"]
    assert unknown == ["bogus"]


# ── Core: agents ─────────────────────────────────────────────────────────────

def test_agents_detect_returns_list():
    from axiom_cli.core.agents import detect
    agents = detect()
    assert isinstance(agents, list)
    names = [a.name for a in agents]
    assert "claude" in names
    assert "codex" in names
    assert "cursor" in names
