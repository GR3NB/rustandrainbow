#!/bin/bash
cd "/Users/ryannortham/Claude/Projects/side business/Rust & Rainbow" || exit 1
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:$PATH"
LOG="/Users/ryannortham/Claude/Projects/side business/Rust & Rainbow/generate.log"
echo "---" >> "$LOG"
echo "$(date '+%Y-%m-%d %H:%M:%S') — starting generate run" >> "$LOG"
python3 agent.py --mode generate --yes >> "$LOG" 2>&1
echo "$(date '+%Y-%m-%d %H:%M:%S') — generate run complete (exit $?)" >> "$LOG"
