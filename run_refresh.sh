#!/bin/bash
cd "/Users/ryannortham/Claude/Projects/side business/Rust & Rainbow" || exit 1
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:$PATH"
LOG="/Users/ryannortham/Claude/Projects/side business/Rust & Rainbow/refresh.log"
echo "---" >> "$LOG"
echo "$(date '+%Y-%m-%d %H:%M:%S') — starting token refresh" >> "$LOG"
python3 refresh_meta_token.py >> "$LOG" 2>&1
echo "$(date '+%Y-%m-%d %H:%M:%S') — refresh complete (exit $?)" >> "$LOG"
