# ARCI — ARC Installer

**ARCI** is the official system installer for ARC-V2.

It handles the initial installation of ARC-V2 Core, prepares required system dependencies, and provides an optional component selection step for installing additional ARC services.

**Linux · Automated installation · Development setup**

## Installation

Clone the repository or obtain `arci.py`, then run:

```bash
python arci.py
```

By default, ARCI installs ARC-V2 Core as a `uv` tool.

## Installation modes

### Production installation

Installs ARC-V2 Core directly from its Git repository using uv:

```bash
python arci.py
```

ARC Core becomes available through the `arc` command.

### Development installation

Clones ARC-V2 Core into the current working directory and installs its development dependencies:

```bash
python arci.py --development
```

The repository is placed in:

```text
./ARC-V2-Core/
```

The target directory must not already exist.

## Options

| Option | Description |
|---|---|
| `-d`, `-dev`, `--development` | Install ARC Core as a development project. |
| `-a`, `-auto`, `--automaticdeps`, `--automatic-deps` | Automatically install missing system dependencies. |
| `-y`, `--yes` | Skip interactive confirmation prompts. |
| `--no-color` | Disable colored terminal output. |
| `-h`, `--help` | Display available options. |

### Examples

```bash
# Standard installation
python arci.py

# Install with automatic dependency handling
python arci.py --automatic-deps

# Non-interactive installation
python arci.py --automatic-deps --yes

# Development installation
python arci.py --development

# Development installation with automatic dependencies
python arci.py --development --automatic-deps
```

## System dependencies

ARCI checks for the tools required to install ARC-V2 Core.

| Dependency | Purpose |
|---|---|
| `uv` | Python package and tool management |
| `git` | Repository cloning and installation |
| `curl` | Required to install uv automatically |

Automatic dependency installation currently supports:

- `apt-get`
- `dnf`
- `pacman`
- `zypper`

When `--automatic-deps` is enabled, ARCI uses the detected package manager to install missing dependencies. This may require `sudo` access.

## Optional ARC components

After installing ARC-V2 Core, ARCI offers an interactive selection of additional ARC components.

Currently available:

| Component | Description |
|---|---|
| Inference Runtime | Local model inference backend for ARC. |

Components are installed through the ARC Core CLI:

```bash
arc install <repository>
```

The inference runtime provides the local inference endpoint. A supported inference model must be configured separately.

Optional component selection requires an interactive terminal. In non-interactive environments, optional components are skipped.

## Initial setup

After installation, ARCI starts ARC Core for its first-time setup:

```bash
arc --autofix
```

In development mode, the equivalent command is executed through:

```bash
uv run arc --autofix
```

## Requirements and limitations

- Linux is currently the only supported operating system.
- ARC-V2 Core requires Python 3.11 or newer.
- Git and uv are required.
- Automatic system dependency installation supports the package managers listed above.
- Inference models and their configuration are handled separately from ARCI.

## ARC-V2

ARCI is part of the ARC-V2 ecosystem.

- [ARC-V2 Organization](https://github.com/ARC-V2-AI)
- [ARC-V2 Core](https://github.com/ARC-V2-AI/ARC-V2-Core)
- [Inference Runtime](https://github.com/ARC-V2-AI/inference-runtime)

**Local-first · Service-oriented · Persistent by design**