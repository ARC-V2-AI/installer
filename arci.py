__version__ = "0.1.1"

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

def attach_terminal_input() -> None:
    """Use the controlling terminal when stdin is occupied by a pipe."""
    if sys.stdin.isatty():
        return

    try:
        sys.stdin = open("/dev/tty", "r", encoding="utf-8")
    except OSError:
        pass

CORE_REPOSITORY = "https://github.com/ARC-V2-AI/ARC-V2-Core.git"
CORE_DIRECTORY = "ARC-V2-Core"

INSTALL_COMMANDS = {
    "apt-get": ["sudo", "apt-get", "install", "-y"],
    "dnf": ["sudo", "dnf", "install", "-y"],
    "pacman": ["sudo", "pacman", "-S", "--needed", "--noconfirm"],
    "zypper": ["sudo", "zypper", "install", "-y"],
}

CORE_COMPONENTS = [
    {
        "name": "Inference Runtime",
        "source": "https://github.com/ARC-V2-AI/inference-runtime.git",
        "description": "Local model inference backend for ARC.",
        "notes": [
            "Provides the local inference endpoint.",
            "A supported inference model must be configured separately.",
        ],
    },

    # Add future ARC components here.
]


# ---------------------------------------------------------------------------
# Terminal interface
# ---------------------------------------------------------------------------

USE_COLOR = False
RESET = "\033[0m"

COLORS = {
    "accent": "\033[96m",
    "purple": "\033[95m",
    "muted": "\033[90m",
    "success": "\033[92m",
    "warning": "\033[93m",
    "error": "\033[91m",
    "bold": "\033[1m",
}


def paint(message: str, *styles: str) -> str:
    if not USE_COLOR:
        return message

    prefix = "".join(COLORS[style] for style in styles)
    return f"{prefix}{message}{RESET}"


def banner() -> None:
    print()
    print(
        f"{paint('ARC-V2', 'accent', 'bold')}  "
        f"{paint('SYSTEM INSTALLER', 'purple', 'bold')}"
    )
    print(paint("Local-first · service-oriented · persistent by design", "muted"))
    print(paint("─" * 58, "muted"))


def section(message: str) -> None:
    print(f"\n{paint('›', 'accent', 'bold')} {paint(message, 'bold')}")


def info(message: str) -> None:
    print(f"{paint('[INFO]', 'accent', 'bold')}    {message}")


def success(message: str) -> None:
    print(f"{paint('[ OK ]', 'success', 'bold')}    {message}")


def warning(message: str) -> None:
    print(f"{paint('[WARN]', 'warning', 'bold')}    {message}")


def error(message: str) -> None:
    print(f"{paint('[FAIL]', 'error', 'bold')}    {message}", file=sys.stderr)

def select_components() -> list[dict]:
    if not CORE_COMPONENTS:
        return []

    if not sys.stdin.isatty():
        warning("Non-interactive terminal. Skipping optional components.")
        return []

    section("Optional ARC Components")

    print("Select the components you want to install:\n")

    for index, component in enumerate(CORE_COMPONENTS, start=1):
        print(f"  [ ] {index}. {component['name']}")
        print(f"      {paint(component['description'], 'muted')}")

        for note in component.get("notes", []):
            print(f"      {paint('Note:', 'warning')} {note}")

        print()

    while True:
        selection = input(
            "Select components (numbers separated by commas, "
            "'all', or Enter to skip): "
        ).strip().lower()

        if not selection:
            return []

        if selection == "all":
            selected = CORE_COMPONENTS.copy()
            break

        try:
            indices = {
                int(value.strip()) - 1
                for value in selection.split(",")
            }

            if any(
                index < 0 or index >= len(CORE_COMPONENTS)
                for index in indices
            ):
                raise ValueError

            selected = [
                component
                for index, component in enumerate(CORE_COMPONENTS)
                if index in indices
            ]

            break

        except ValueError:
            warning("Invalid selection. Enter valid component numbers.")

    print("\nSelected components:")

    for component in selected:
        success(component["name"])

    return selected


# ---------------------------------------------------------------------------
# System utilities
# ---------------------------------------------------------------------------

def is_installed(program: str) -> bool:
    return shutil.which(program) is not None


def add_to_path(directory: str | Path) -> None:
    path = str(Path(directory).expanduser())
    current = os.environ.get("PATH", "").split(os.pathsep)

    if path not in current:
        os.environ["PATH"] = os.pathsep.join([path, *current])


def run_command(
    command: list[str],
    cwd: str | Path | None = None,
    show_output: bool = False,
) -> str:
    try:
        result = subprocess.run(
            command,
            capture_output=not show_output,
            text=True,
            cwd=cwd,
            check=False,
        )
    except FileNotFoundError as exc:
        raise RuntimeError(f"Required command not found: {command[0]}") from exc

    if result.returncode != 0:
        if not show_output:
            details = (result.stderr or result.stdout or "").strip()
            if details:
                error(details)

        error(f"Command failed with exit code {result.returncode}: {command[0]}")

        raise subprocess.CalledProcessError(
            result.returncode,
            command,
            output=result.stdout,
            stderr=result.stderr,
        )

    return result.stdout or ""


# ---------------------------------------------------------------------------
# Dependency management
# ---------------------------------------------------------------------------

def get_manager() -> str:
    for manager in INSTALL_COMMANDS:
        if is_installed(manager):
            return manager

    raise RuntimeError(
        "No supported package manager found "
        "(apt-get, dnf, pacman, zypper)."
    )


def install_package(package: str) -> None:
    manager = get_manager()

    info(f"Using package manager: {manager}")

    if manager == "apt-get":
        info("Refreshing package lists...")
        run_command(["sudo", "apt-get", "update"], show_output=True)

    info(f"Installing system dependency: {package}")

    run_command(
        [*INSTALL_COMMANDS[manager], package],
        show_output=True,
    )

    success(f"Installed {package}")


def ensure_dependency(program: str, automatic_deps: bool) -> None:
    if is_installed(program):
        success(f"Found {program}")
        return

    warning(f"{program} is not installed")

    if not automatic_deps:
        raise RuntimeError(
            f"{program} is required. "
            "Re-run with --automatic-deps to install it automatically."
        )

    install_package(program)

    if not is_installed(program):
        raise RuntimeError(
            f"{program} installation completed, "
            "but the executable was not found."
        )


def install_uv(automatic_deps: bool) -> None:
    section("Installing uv")

    ensure_dependency("curl", automatic_deps)

    info("Running the official uv installer...")

    run_command(
        ["sh", "-c", "curl -LsSf https://astral.sh/uv/install.sh | sh"],
        show_output=True,
    )

    # The installer normally places uv in ~/.local/bin.
    add_to_path(Path.home() / ".local" / "bin")

    if not is_installed("uv"):
        raise RuntimeError(
            "uv was installed, but could not be found in ~/.local/bin or PATH."
        )

    success("uv is ready")


def install_components(
    components: list[dict],
    development: bool,
) -> None:
    if not components:
        info("No optional components selected.")
        return

    section("Installing ARC Components")

    arc_command = (
        ["uv", "run", "arc"]
        if development
        else ["arc"]
    )

    for component in components:
        info(f"Installing {component['name']}...")

        command = [
            *arc_command,
            "install",
            component["source"],
        ]

        run_command(command, show_output=True)

        success(f"{component['name']} installed")



# ---------------------------------------------------------------------------
# ARC Core installation
# ---------------------------------------------------------------------------

def run_first_start(cwd: str | Path | None = None) -> None:
    section("Starting ARC Core for first-time setup")

    info("ARC Core will now run its first-start setup.")
    info("Press Ctrl+C to stop the process.")

    command = (
        ["uv", "run", "arc", "--autofix"]
        if cwd
        else ["arc", "--autofix"]
    )

    run_command(command, cwd=cwd, show_output=True)


def dev_install_core() -> None:
    target = Path.cwd() / CORE_DIRECTORY

    if target.exists() or target.is_symlink():
        raise FileExistsError(
            f"Installation directory already exists: {target}"
        )

    section("Cloning ARC Core")

    info(f"Destination: {target}")

    run_command(
        ["git", "clone", CORE_REPOSITORY, str(target)],
        show_output=True,
    )

    success("ARC Core repository cloned")

    section("Installing project dependencies")

    run_command(
        ["uv", "sync"],
        cwd=target,
        show_output=True,
    )

    success("Project dependencies installed")
    success("Development installation completed")


def production_install_core() -> None:
    section("Installing ARC Core")

    run_command(
        ["uv", "tool", "install", f"git+{CORE_REPOSITORY}"],
        show_output=True,
    )

    success("ARC Core installed as a uv tool")

    # Resolve uv's configured executable directory.
    tool_bin = run_command(["uv", "tool", "dir", "--bin"]).strip()

    if tool_bin:
        add_to_path(tool_bin)

    if not is_installed("arc"):
        raise RuntimeError(
            "ARC Core was installed, but the 'arc' command "
            "is not available on PATH."
        )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def confirm(message: str, assume_yes: bool) -> bool:
    if assume_yes:
        info("Confirmation skipped (--yes)")
        return True

    try:
        answer = input(
            f"\n{paint('[CONFIRM]', 'warning', 'bold')} "
            f"{message} [y/N] "
        ).strip().lower()
    except EOFError as exc:
        raise RuntimeError(
            "Interactive confirmation unavailable. "
            "Re-run with --yes to proceed."
        ) from exc

    return answer in {"y", "yes"}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="arci",
        description="Install ARC-V2 Core for development or as a system tool.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python arci.py                  Install ARC Core as a uv tool\n"
            "  python arci.py --development    Development installation\n"
            "  python arci.py --automatic-deps --yes\n"
        ),
    )

    parser.add_argument(
    "-V", "--version",
    action="version",
        version=f"%(prog)s {__version__}",
    )

    parser.add_argument(
        "-d", "-dev", "--development",
        action="store_true",
        help="Clone ARC Core and install its development dependencies.",
    )

    parser.add_argument(
        "-a", "-auto", "--automaticdeps", "--automatic-deps",
        dest="automatic_deps",
        action="store_true",
        help="Automatically install missing system dependencies.",
    )

    parser.add_argument(
        "-y", "--yes",
        action="store_true",
        help="Skip interactive confirmation prompts.",
    )

    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable colored terminal output.",
    )

    return parser


def main() -> int:
    global USE_COLOR

    parser = build_parser()
    args = parser.parse_args()
    
    attach_terminal_input()

    USE_COLOR = (
        sys.stdout.isatty()
        and "NO_COLOR" not in os.environ
        and not args.no_color
    )

    banner()

    if sys.platform != "linux":
        raise RuntimeError("The ARC-V2 installer currently supports Linux only.")

    section("Checking system dependencies")

    if is_installed("uv"):
        success("Found uv")
    else:
        warning("uv is not installed")

        if not args.automatic_deps:
            raise RuntimeError(
                "uv is required. Re-run with --automatic-deps to install it."
            )

        install_uv(args.automatic_deps)

    ensure_dependency("git", args.automatic_deps)

    if args.development:
        target = Path.cwd() / CORE_DIRECTORY

        info(f"Development installation target: {target}")

        if not confirm(
            "Proceed with ARC Core development installation?",
            args.yes,
        ):
            warning("Installation cancelled")
            return 0

        dev_install_core()

    else:
        production_install_core()


    # Optional component installation
    components = select_components()

    install_components(
        components,
        development=args.development,
    )


    # First ARC Core startup
    run_first_start(
        cwd=Path.cwd() / CORE_DIRECTORY
        if args.development
        else None
    )


if __name__ == "__main__":
    try:
        raise SystemExit(main())

    except KeyboardInterrupt:
        error("Operation interrupted by user")
        raise SystemExit(130)

    except subprocess.CalledProcessError:
        raise SystemExit(1)

    except (RuntimeError, OSError) as exc:
        error(str(exc))
        raise SystemExit(1)
