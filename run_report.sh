#!/bin/bash
# Weekly report + Etsy optimisation — runs Monday at 7:00am via launchd
# Generates AI narrative, tracks performance_log.json, auto-rewrites zero-traffic listings

PROJ="/Users/ryannortham/Claude/Projects/side business/Rust & Rainbow"
LOG="$PROJ/report.log"

cd "$PROJ" || { echo "$(date '+%Y-%m-%d %H:%M:%S') — ERROR: project directory not found" >> "$LOG"; exit 1; }
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:$PATH"

echo "---" >> "$LOG"
echo "$(date '+%Y-%m-%d %H:%M:%S') — starting weekly report" >> "$LOG"
python3 agent.py --mode report --yes >> "$LOG" 2>&1
echo "$(date '+%Y-%m-%d %H:%M:%S') — report complete (exit $?)" >> "$LOG"
