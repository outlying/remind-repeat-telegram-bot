#!/usr/bin/env bash
set -e

# If START_CMD is empty, use the default
: "${START_CMD:=python main.py}"

# Optional pre-start hook (migrations, create folders, etc.)
# ...existing code...

# Exec so the app becomes PID 1 and receives signals properly
exec sh -c "$START_CMD"
