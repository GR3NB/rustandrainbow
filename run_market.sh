#!/bin/bash
# run_market.sh — called by launchd for automated Rust & Rainbow social posting
# Runs agent.py --mode market --yes with logging

# Change to the project directory so .env and designs_log.json are found
cd "/Users/ryannortham/Claude/Projects/side business/Rust & Rainbow" || exit 1

# Log file — rotates are handled manually; feel free to trim periodically
LOG="/Users/ryannortham/Claude/Projects/side business/Rust & Rainbow/market.log"

# Add Homebrew to PATH (covers both Intel and Apple Silicon Macs)
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:$PATH"

echo "---" >> "$LOG"
echo "$(date '+%Y-%m-%d %H:%M:%S') — starting market run" >> "$LOG"

python3 agent.py --mode market --yes >> "$LOG" 2>&1

echo "$(date '+%Y-%m-%d %H:%M:%S') — market run complete (exit $?)" >> "$LOG"
