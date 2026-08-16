#!/usr/bin/env bash
set -euo pipefail

# Bootstrap Nomad Lakehouse on Ubuntu
echo "🚀 Bootstrapping Nomad Lakehouse..."

# 1. Ensure prerequisites
for cmd in docker python3 npm; do
    if ! command -v $cmd &> /dev/null; then
        echo "Error: $cmd is not installed."
        exit 1
    fi
done

# 2. Setup env
if [[ ! -f .env ]]; then
    cp .env.example .env
fi

# 3. Interactive Setup Wizard (NPM-based TUI)
echo "⚙️ Launching setup wizard..."
cd tui
npm install
npm run start
cd ..

# 4. Bootstrap core services
echo "📦 Starting core services..."
sudo ./scripts/setup_minio.sh

# 5. Initialize Python environment
echo "🐍 Setting up Python environment..."
INSTALL_PROFILE=lakehouse ./scripts/setup_python_env.sh

echo "✅ Bootstrap complete! Run 'source .venv/bin/activate' to start working."
