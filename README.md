# axiom-cli

CLI orchestrator for the axiom ecosystem — bootstrap AI-ready projects in one command.

## What it does

`axiom` ties together three components that live in `~/AI-Ecosystem/`:

| Component | Role |
|---|---|
| **continuum** | Persistent memory system (postgres + redis + MCP server) |
| **axiom-team** | 7 specialised AI agents + project templates |
| **axiom-skills** | 15 skill definition files (react, tailwindcss, postgresql, …) |

## Installation

**Requirements:** Python 3.12+, [uv](https://docs.astral.sh/uv/)

```bash
# from the axiom-cli directory
uv tool install .
```

This installs the `axiom` binary globally.

## Quick start

```bash
# 1. One-time machine setup — starts continuum, verifies MCP
axiom init

# 2. Create a new project
axiom new my-app

# 3. Create a project with a specific stack
axiom new my-app --stack react,tailwindcss,postgresql

# 4. Install axiom into an existing project
cd existing-project
axiom install --skills react,typescript

# 5. Health check
axiom status

# 6. Pull latest ecosystem updates
axiom update

# 7. Diagnose problems
axiom doctor
```

## Commands

### `axiom init [--ecosystem-root PATH]`

Run once per machine. Starts continuum containers, waits for postgres and redis to be
healthy, verifies the continuum MCP server, and prints per-agent MCP configuration
instructions.

Pass `--ecosystem-root` to override the default `~/AI-Ecosystem` path (saved to
`~/.axiom/config.yaml`).

### `axiom new <project-name> [--stack SKILLS]`

Creates `<project-name>/`, runs `git init`, and installs the axiom-team templates and
skills via `install.sh`. `--stack` accepts a comma-separated list of skill names
(e.g. `react,tailwindcss,postgresql`). Unknown skill names are warned and skipped.

### `axiom install [--skills SKILLS] [--force]`

Installs axiom into the **current directory**. Same as `new` but for existing projects.
`--force` overwrites already-installed files.

### `axiom status`

Prints a health-check table:

```
✅  Docker installed
✅  Docker daemon running
✅  Continuum postgres healthy   memory-ai-postgres-1
✅  Continuum redis healthy      memory-ai-redis-1
✅  Ecosystem repo: continuum    ~/AI-Ecosystem/continuum
✅  Ecosystem repo: axiom-team   ~/AI-Ecosystem/axiom-team
✅  Ecosystem repo: axiom-skills ~/AI-Ecosystem/axiom-skills
✅  Continuum MCP server starts
❌  Current dir has .axiom/ installed
```

### `axiom update`

Runs `git pull` in each of the three ecosystem repos. If the current directory has
`.axiom/` installed, suggests running `axiom install --force` to pick up changes.

### `axiom doctor`

Full diagnostic tool. For every problem it detects, it prints the exact command to fix
it — including per-agent MCP configuration snippets.

## Configuration

Config lives at `~/.axiom/config.yaml` and is created automatically on first use.

```yaml
ecosystem_root: ~/AI-Ecosystem
```

Override the ecosystem path:

```bash
axiom init --ecosystem-root /path/to/my/AI-Ecosystem
```

## Development

```bash
uv sync           # install deps
uv run pytest -v  # run tests
uv run axiom      # run from source
```
