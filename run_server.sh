#!/bin/bash

# Script to activate venv and run the fastmcp server
# This script can be used by gemini-cli which requires a single command

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/.venv"
SERVER_SCRIPT="$SCRIPT_DIR/mcp_server.py"

# Check if venv exists
if [ ! -d "$VENV_DIR" ]; then
    echo "Error: Virtual environment not found at $VENV_DIR" >&2
    exit 1
fi

# Check if mcp_server.py exists
if [ ! -f "$SERVER_SCRIPT" ]; then
    echo "Error: mcp_server.py not found at $SERVER_SCRIPT" >&2
    exit 1
fi

# Use venv's Python to run the server directly
# This avoids needing to source activate, which doesn't work well in scripts
exec "$VENV_DIR/bin/python" "$SERVER_SCRIPT"

