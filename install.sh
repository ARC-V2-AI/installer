#!/usr/bin/env bash
set -Eeuo pipefail

# ARC-V2 bootstrap installer.
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/ARC-V2-AI/installer/main/install.sh | bash
#   curl -fsSL https://raw.githubusercontent.com/ARC-V2-AI/installer/main/install.sh | bash -s -- --development --automatic-deps

readonly ARCI_URL="https://raw.githubusercontent.com/ARC-V2-AI/installer/main/arci.py"

DEVELOPMENT=0
MODE_SET=0
AUTOMATIC_DEPS=0
ASSUME_YES=0
NO_COLOR=0

usage() {
    cat <<'USAGE'
ARC-V2 Installer bootstrap

Usage:
  install.sh [OPTIONS]

Options:
  --development       Install ARC Core as a development checkout.
  --production        Install ARC Core as a uv user tool (default).
  --automatic-deps    Automatically install missing system dependencies.
  --yes               Skip installer confirmation prompts.
  --no-color          Disable installer colors.
  -h, --help          Show this help.

Examples:
  curl -fsSL https://raw.githubusercontent.com/ARC-V2-AI/installer/main/install.sh | bash
  curl -fsSL https://raw.githubusercontent.com/ARC-V2-AI/installer/main/install.sh | bash -s -- --development
  curl -fsSL https://raw.githubusercontent.com/ARC-V2-AI/installer/main/install.sh | bash -s -- --automatic-deps --yes
USAGE
}

fail() {
    printf 'Error: %s\n' "$*" >&2
    exit 1
}

for arg in "$@"; do
    case "$arg" in
        --development)
            [[ "$MODE_SET" -eq 0 || "$DEVELOPMENT" -eq 1 ]] || fail "Choose only one of --development or --production."
            DEVELOPMENT=1
            MODE_SET=1
            ;;
        --production)
            [[ "$MODE_SET" -eq 0 || "$DEVELOPMENT" -eq 0 ]] || fail "Choose only one of --development or --production."
            DEVELOPMENT=0
            MODE_SET=1
            ;;
        --automatic-deps)
            AUTOMATIC_DEPS=1
            ;;
        --yes)
            ASSUME_YES=1
            ;;
        --no-color)
            NO_COLOR=1
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            fail "Unknown option: $arg (use --help for usage)."
            ;;
    esac
done

# With curl | bash, stdin contains this script. Read interactive answers from
# the controlling terminal instead of stdin.
have_tty=0
if [[ -r /dev/tty && -w /dev/tty ]]; then
    have_tty=1
fi

ask() {
    local prompt="$1"
    local answer_var="$2"
    local answer=""

    if [[ "$have_tty" -eq 0 ]]; then
        printf -v "$answer_var" '%s' ""
        return 1
    fi

    printf '%s' "$prompt" > /dev/tty
    IFS= read -r answer < /dev/tty || answer=""
    printf -v "$answer_var" '%s' "$answer"
}

if [[ "$MODE_SET" -eq 0 && "$ASSUME_YES" -eq 0 && "$have_tty" -eq 1 ]]; then
    printf '\nARC-V2 Installer\n\n' > /dev/tty
    printf '  1) User / Production (default)\n  2) Development\n\n' > /dev/tty
    if ask 'Select installation mode [1/2]: ' mode; then
        case "${mode,,}" in
            ''|1|production|prod|user)
                DEVELOPMENT=0
                ;;
            2|development|dev)
                DEVELOPMENT=1
                ;;
            *)
                fail "Invalid installation mode: $mode"
                ;;
        esac
    fi
fi

if [[ "$AUTOMATIC_DEPS" -eq 0 && "$ASSUME_YES" -eq 0 && "$have_tty" -eq 1 ]]; then
    if ask 'Automatically install missing system dependencies? [y/N]: ' deps_answer; then
        case "${deps_answer,,}" in
            y|yes) AUTOMATIC_DEPS=1 ;;
            *)     AUTOMATIC_DEPS=0 ;;
        esac
    fi
fi

command -v curl >/dev/null 2>&1 || fail "curl is required to download the ARC installer."
command -v python3 >/dev/null 2>&1 || fail "python3 is required to run the ARC installer."

if [[ "$DEVELOPMENT" -eq 1 ]]; then
    printf '\nSelected mode: Development\n'
else
    printf '\nSelected mode: User / Production\n'
fi
if [[ "$AUTOMATIC_DEPS" -eq 1 ]]; then
    printf 'Automatic system dependencies: enabled\n'
else
    printf 'Automatic system dependencies: disabled\n'
fi

work_dir="$(mktemp -d "${TMPDIR:-/tmp}/arci.XXXXXXXX")"
cleanup() {
    rm -rf -- "$work_dir"
}
trap cleanup EXIT

installer_file="$work_dir/arci.py"
printf '\nDownloading ARC Installer...\n'
curl --fail --silent --show-error --location \
    --retry 3 --connect-timeout 15 \
    --proto '=https' --tlsv1.2 \
    "$ARCI_URL" -o "$installer_file"

[[ -s "$installer_file" ]] || fail "The downloaded installer is empty."

installer_args=()
if [[ "$DEVELOPMENT" -eq 1 ]]; then
    installer_args+=(--development)
fi
if [[ "$AUTOMATIC_DEPS" -eq 1 ]]; then
    installer_args+=(--automatic-deps)
fi
if [[ "$ASSUME_YES" -eq 1 ]]; then
    installer_args+=(--yes)
fi
if [[ "$NO_COLOR" -eq 1 ]]; then
    installer_args+=(--no-color)
fi

printf 'Starting ARCI...\n\n'

if [[ "$have_tty" -eq 1 ]]; then
    python3 "$installer_file" "${installer_args[@]}" </dev/tty
else
    python3 "$installer_file" "${installer_args[@]}"
fi
