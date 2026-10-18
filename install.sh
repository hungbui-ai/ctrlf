#!/usr/bin/env bash
# ctrlf One-line Installer
set -euo pipefail

echo "⚡ Installing ctrlf (AI Agent Code Locator & Surgical Editor)..."

INSTALL_DIR="${HOME}/.local/bin"
mkdir -p "${INSTALL_DIR}"

# Check python3
if ! command -v python3 >/dev/null 2>&1; then
    echo "❌ Error: Python 3.9+ is required." >&2
    exit 1
fi

# Clone or install via pip
if command -v pip3 >/dev/null 2>&1; then
    pip3 install --user --upgrade git+https://github.com/hungbui-ai/ctrlf.git
else
    pip install --user --upgrade git+https://github.com/hungbui-ai/ctrlf.git
fi

echo "✔ Successfully installed ctrlf and ctrlf-mcp."
echo "Running auto-installer to configure detected AI agents (Cursor, Claude Code, Antigravity)..."
"${INSTALL_DIR}/ctrlf" init || true

echo "🎉 All set! Your coding agents will now use ctrlf for 90-95% token savings."
