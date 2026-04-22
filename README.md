# axiom-cli

CLI orchestrator for the axiom ecosystem — bootstrap AI-ready projects in one command.

## What it does

`axiom` clones and manages three components from GitHub and wires them together on your machine:

| Component | Repository | Role |
|---|---|---|
| **continuum** | [hhcarmenate/continuum](https://github.com/hhcarmenate/continuum) | Persistent memory system (postgres + redis + MCP server) |
| **axiom-team** | [hhcarmenate/axiom-team](https://github.com/hhcarmenate/axiom-team) | 7 specialised AI agents + project templates |
| **axiom-skills** | [hhcarmenate/axiom-skills](https://github.com/hhcarmenate/axiom-skills) | 15 skill definition files (react, tailwindcss, postgresql, …) |

## How it works

axiom has two layers — one global, one per project:

```
~/AI-Ecosystem/          ← cloned once per machine (global)
├── continuum/           ← postgres + redis + MCP server (shared across all projects)
├── axiom-team/          ← agent definitions (source of truth)
└── axiom-skills/        ← skill definitions (source of truth)

your-project/            ← your actual project
└── .axiom/              ← installed by axiom new / axiom install (per project)
    ├── agents/          ← copied from axiom-team
    └── skills/          ← copied from axiom-skills
```

`axiom init` sets up the global layer once. `axiom new` / `axiom install` set up the
per-project layer. Continuum's memory is shared across all projects by design — that is
what gives your AI agents persistent context across sessions and codebases.

By default the repos are cloned into `~/AI-Ecosystem/`. You can override this with `--ecosystem-root`.

## Installation

**Requirements:** Python 3.12+, [uv](https://docs.astral.sh/uv/), Docker

```bash
# from the axiom-cli directory
uv tool install .
```

This installs the `axiom` binary globally.

## Quick start

```bash
# 1. One-time machine setup — clones ecosystem repos, starts continuum, verifies MCP
axiom init --clone

# 2. Create a new project
axiom new my-app

# 3. Create a project with a specific stack
axiom new my-app --stack react,tailwindcss,postgresql

# 4. Install axiom into an existing project
cd existing-project
axiom install --skills react,typescript

# 5. Health check
axiom status

# 6. Pull latest updates from GitHub
axiom update

# 7. Diagnose problems
axiom doctor
```

## Commands

### `axiom init [--clone] [--ecosystem-root PATH]`

Run once per machine. Checks that the three ecosystem repos are present locally and, with
`--clone`, clones any that are missing directly from GitHub. Then starts continuum
containers, waits for postgres and redis to be healthy, verifies the continuum MCP server,
and prints per-agent MCP configuration instructions.

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

Runs `git pull` in each of the three ecosystem repos, fetching the latest changes from
GitHub. If the current directory has `.axiom/` installed, suggests running
`axiom install --force` to pick up changes.

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
axiom init --ecosystem-root /path/to/my/ecosystem
```

## Development

```bash
uv sync           # install deps
uv run pytest -v  # run tests
uv run axiom      # run from source
```
