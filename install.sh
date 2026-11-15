#!/usr/bin/env bash
# OctoFlow 1-Line Installer
# Installs OctoFlow cephalopod multi-agent coding engine and CLI.

set -e

echo "◈ Installing OctoFlow Cephalopod Connectome..."

# Verify Python 3.10+
if command -v python3 >/dev/null 2>&1; then
    PY_VER=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    PY_MAJOR=$(echo "$PY_VER" | cut -d. -f1)
    PY_MINOR=$(echo "$PY_VER" | cut -d. -f2)
    if [ "$PY_MAJOR" -lt 3 ] || ([ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -lt 10 ]); then
        echo "✗ Error: Python 3.10 or higher is required (found Python $PY_VER)."
        exit 1
    fi
else
    echo "✗ Error: Python 3 is not installed. Please install Python 3.10+ first."
    exit 1
fi

INSTALL_DIR="${HOME}/.octoflow/pkg"
BIN_DIR="${HOME}/.local/bin"

mkdir -p "$INSTALL_DIR"
mkdir -p "$BIN_DIR"

if command -v pipx >/dev/null 2>&1; then
    echo "◈ Using pipx for isolated global installation..."
    pipx install --force git+https://github.com/Sachinrameshvd/octoflow.git
else
    echo "◈ Creating dedicated virtualenv at $INSTALL_DIR..."
    python3 -m venv "$INSTALL_DIR/venv"
    "$INSTALL_DIR/venv/bin/pip" install --upgrade pip setuptools wheel -q
    "$INSTALL_DIR/venv/bin/pip" install git+https://github.com/Sachinrameshvd/octoflow.git -q
    
    ln -sf "$INSTALL_DIR/venv/bin/octos" "$BIN_DIR/octos"
    ln -sf "$INSTALL_DIR/venv/bin/octoflow" "$BIN_DIR/octoflow"
    
    case ":$PATH:" in
        *":$BIN_DIR:"*) ;;
        *)
            echo "▲ Notice: Add $BIN_DIR to your PATH in ~/.bashrc or ~/.zshrc:"
            echo "   export PATH=\"\$HOME/.local/bin:\$PATH\""
            ;;
    esac
fi

echo "✓ OctoFlow installed successfully!"
echo "◈ Launch cockpit with: octos"
echo "◈ Or run a simulation: octos run \"Build a rate limiter\" --provider mock"
