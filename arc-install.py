import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

INSTALL_COMMANDS = {
        "apt-get": ["sudo", "apt-get", "install", "-y"],
        "dnf": ["sudo", "dnf", "install", "-y"],
        "pacman": ["sudo", "pacman", "-Sy", "--needed", "--noconfirm"],
        "zypper": ["sudo", "zypper", "install", "-y"],
    }


def prRed(s): print(f"\033[91m {s}\033[00m")
def prGreen(s): print(f"\033[92m {s}\033[00m")
def prYellow(s): print(f"\033[93m {s}\033[00m")
def prLightPurple(s): print(f"\033[94m {s}\033[00m")
def prPurple(s): print(f"\033[95m {s}\033[00m")
def prCyan(s): print(f"\033[96m {s}\033[00m")


def is_installed(program: str) -> bool:
    return shutil.which(program) is not None

def run_command(
    command: list[str],
    cwd: str | Path | None = None,
    show_output: bool = False
) -> str:
    result = subprocess.run(
        command,
        capture_output=not show_output,
        text=True,
        cwd=cwd,
        check=False
    )

    if result.returncode != 0:
        prRed(result.stderr or "Command failed.")
        raise subprocess.CalledProcessError(
            result.returncode,
            command,
            output=result.stdout,
            stderr=result.stderr
        )

    return result.stdout or ""


def get_manager() -> str|None:
    managers = ["apt-get","dnf","pacman","zypper"]

    for manager in managers:
        if shutil.which(manager):
            return manager
    
    
    raise RuntimeError("Unsupported Linux package manager")

def install_package(pkg: str):
    _mngr = get_manager()
    prYellow(_mngr)
    if _mngr == "apt-get":
        prLightPurple("[I] Running apt-get update...")
        run_command(["sudo", "apt-get", "update"])

    _i_cmd = INSTALL_COMMANDS.get(_mngr).copy()
    _i_cmd.append(pkg)

    prLightPurple(f"[I] Installing {pkg} using {_mngr}")
    run_command(pkg)
    prGreen(f"[+] Completed {pkg} install")



def install_uv(auto: bool):
    prLightPurple("[] Installing UV...")
    if not is_installed("curl"): 
        if not auto:
            raise RuntimeError("curl is required to install uv")
    
        install_package("curl")

    run_command(["sh", "-c", "curl -LsSf https://astral.sh/uv/install.sh | sh"])
    prGreen("[+] uv installed")
    prLightPurple("[I] Adding uv to current python PATH...")
    os.environ["PATH"] += os.pathsep + os.path.expanduser("~/.local/bin")

def dev_install_core():
    target = Path.cwd() / "ARC-V2-Core"

    prLightPurple("[I] Installing ARC Core...")

    if target.exists():
        raise FileExistsError(
            f"Installation directory already exists: {target}"
        )

    run_command([
        "git",
        "clone",
        "https://github.com/ARC-V2-AI/ARC-V2-Core.git",
        str(target)
    ])

    prGreen("[+] Completed ARC Core clone")

    prLightPurple("[I] Installing Core dependencies...")

    run_command(["uv", "sync"], cwd=target)

    prGreen("[+] ARC Core dependencies installed!")

    prGreen("[+] ARC Core development installation completed!")


    print()
    print("-"*50)

    prRed("[I] The following starts ARC Core for the first time. It will automatically setup its own environment. Use 'strg-c' to stop. Stoping throws an expected error.")
    prLightPurple("[I] Running ARC Core autofix...")

    run_command(
        ["uv", "run", "arc", "--autofix"],
        cwd=target,
        show_output=True
    )


if __name__ == '__main__':
    if sys.platform != "linux":
        raise RuntimeError("Linux only")
    
    parser = argparse.ArgumentParser(description="ARC-V2's installer script to help with setup for dev or prod.")
    parser.add_argument("-dev", "--development",action="store_true", help="Install for development")
    parser.add_argument("-auto", "--automaticdeps", action="store_true",help="Automatically install missing dependencies")
    
    args = parser.parse_args()

    dev = bool(args.development)
    auto = bool(args.automaticdeps)

    if not is_installed("uv"):
        prYellow("[-] uv is not installed!")

        if auto:
            install_uv(auto)

        raise RuntimeError("uv is not installed run with '-auto' to install.")
    
    if not is_installed("git") and not dev:
        prYellow("[-] git is not installed!")

        if auto:
            install_package("git")
        
        raise RuntimeError("git is not installed run with '-auto' to install.")

    if dev:

        prCyan(f"[I] ARC Core is going to be installed in the current directory: {Path.cwd() / "ARC-V2-Core"}")
        input("\033[91m Press Enter to proceed!\033[00m")

        dev_install_core()


    else:
        prLightPurple("[I] Installing ARC Core as uv system tool...")
        run_command(["uv", "tool", "install", "git+https://github.com/ARC-V2-AI/ARC-V2-Core.git"])
        prGreen("[+] Completed ARC Core install")

        prRed("[I] The following starts ARC Core for the first time. It will automatically setup its own environment. Use 'strg-c' to stop. Stoping throws an expected error.")
        prLightPurple("[I] Running ARC Core autofix...")

        run_command(
            ["arc", "--autofix"],
            show_output=True
        )
