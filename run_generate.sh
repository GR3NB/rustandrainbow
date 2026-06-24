#!/bin/bash
cd "/Users/ryannortham/Claude/Projects/side business/Rust & Rainbow" || exit 1
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:$PATH"
LOG="/Users/ryannortham/Claude/Projects/side business/Rust & Rainbow/generate.log"
echo "---" >> "$LOG"
echo "$(date '+%Y-%m-%d %H:%M:%S') — starting generate run" >> "$LOG"
# Use the project venv (Python 3.11) — system python3 is 3.9 and cannot run rembg,
# which silently disables background removal on newly generated designs.
"/Users/ryannortham/Claude/Projects/side business/Rust & Rainbow/.venv-bgfix/bin/python" agent.py --mode generate --yes >> "$LOG" 2>&1
rc=$?
echo "$(date '+%Y-%m-%d %H:%M:%S') — generate run complete (exit $rc)" >> "$LOG"
# Exit with the python process's real code (not the echo's 0) so a crash is
# visible to launchd / any watchdog instead of being silently masked as success.
exit $rc
