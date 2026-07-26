#!/bin/sh
# Quick test runner: activates the venv (if present) and runs the full suite.
# Usage: sh claude_tools/run_tests.sh
cd "$(dirname "$0")/.." || exit 1
if [ -d venv ]; then
    . venv/bin/activate
fi
python -m pytest pixelart_mcp/tests/ -v
