#!/usr/bin/env bash
set -euo pipefail

echo "🚀 Bootstrapping Nomad Lakehouse..."

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TUI_DIR="$REPO_ROOT/tui"

require_cmd() {
    local cmd="$1"
    if ! command -v "$cmd" >/dev/null 2>&1; then
        echo "Error: required command '$cmd' is not installed."
        exit 1
    fi
}

is_wsl() {
    grep -qi microsoft /proc/version 2>/dev/null
}

is_windows_path() {
    local p="$1"
    [[ "$p" == /mnt/* ]] || [[ "$p" == *"\\"* ]]
}

echo "📍 Repo root: $REPO_ROOT"

# 1. Ensure base prerequisites
require_cmd docker
require_cmd python3

# 2. Validate TUI directory exists
if [[ ! -d "$TUI_DIR" ]]; then
    echo "Error: TUI directory not found at: $TUI_DIR"
    exit 1
fi

# 3. Setup env
if [[ ! -f "$REPO_ROOT/.env" ]]; then
    if [[ -f "$REPO_ROOT/.env.example" ]]; then
        cp "$REPO_ROOT/.env.example" "$REPO_ROOT/.env"
        echo "📝 Created .env from .env.example"
    else
        echo "Warning: .env.example not found, skipping .env creation"
    fi
fi

# 4. Runtime checks for the TUI
echo "⚙️ Checking TUI runtime..."

if is_wsl; then
    echo "🪟 Detected WSL"
fi

USE_BUN=0
if command -v bun >/dev/null 2>&1; then
    BUN_PATH="$(command -v bun)"
    if is_windows_path "$BUN_PATH"; then
        echo "Error: bun resolves to a Windows-mounted path: $BUN_PATH"
        echo "Please install/use Bun inside WSL/Linux."
        exit 1
    fi
    USE_BUN=1
fi

if [[ "$USE_BUN" -eq 0 ]]; then
    require_cmd node
    require_cmd npm
    require_cmd npx

    NODE_PATH="$(command -v node)"
    NPM_PATH="$(command -v npm)"
    NPX_PATH="$(command -v npx)"

    echo "node: $NODE_PATH"
    echo "npm : $NPM_PATH"
    echo "npx : $NPX_PATH"

    if is_windows_path "$NODE_PATH" || is_windows_path "$NPM_PATH" || is_windows_path "$NPX_PATH"; then
        echo "Error: Windows Node/npm/npx detected from inside WSL."
        echo "Please use Linux-native Node or install Bun in WSL."
        exit 1
    fi

    NODE_VERSION="$(node -p 'process.versions.node')"
    echo "Node version: $NODE_VERSION"
fi

# 5. Interactive Setup Wizard
echo "⚙️ Launching setup wizard..."
pushd "$TUI_DIR" >/dev/null

export TERM="${TERM:-xterm-256color}"

if [[ "$USE_BUN" -eq 1 ]]; then
    echo "Using Bun for OpenTUI"
    rm -rf node_modules package-lock.json bun.lockb
    bun install
    bun run src/index.tsx
else
    echo "Using Node/npm for OpenTUI"

    NODE_MAJOR="$(node -p 'process.versions.node.split(".")[0]')"

    if (( NODE_MAJOR < 26 )); then
        echo "Error: OpenTUI native renderer under Node requires a newer Node runtime."
        echo "Detected Node $NODE_VERSION."
        echo "Recommended fixes:"
        echo "  1) Install Bun in WSL and rerun bootstrap, or"
        echo "  2) Use Node 26+ with experimental FFI support."
        popd >/dev/null
        exit 1
    fi

    rm -rf node_modules package-lock.json
    npm install
    node --experimental-ffi node_modules/tsx/dist/cli.mjs src/index.tsx
fi

popd >/dev/null

# 6. Bootstrap core services
echo "📦 Starting core services..."
sudo "$REPO_ROOT/scripts/setup_minio.sh"

# 7. Initialize Python environment
echo "🐍 Setting up Python environment..."
INSTALL_PROFILE=lakehouse "$REPO_ROOT/scripts/setup_python_env.sh"

echo "✅ Bootstrap complete! Run 'source .venv/bin/activate' to start working."
