#!/bin/bash
set -euo pipefail

# Only run in remote (Claude Code on the web) environments
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

cd "$CLAUDE_PROJECT_DIR"

# Install runtime and dev dependencies using the system Python's pip
python3 -m pip install -r requirements.txt
python3 -m pip install -r requirements-dev.txt
