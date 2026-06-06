#!/bin/bash
# watchdog.sh — Rust & Rainbow post watchdog
# Runs 10 minutes after the launchd post job (10:10am Mon/Wed/Fri).
# If the log file was not updated today, fires a macOS notification.

LOG="/Users/ryannortham/Claude/Projects/side business/Rust & Rainbow/market.log"
TODAY=$(date +%Y-%m-%d)
LAST_MODIFIED=$(stat -f %Sm -t %Y-%m-%d "$LOG" 2>/dev/null)

if [ "$LAST_MODIFIED" != "$TODAY" ]; then
    osascript -e 'display notification "Check market.log in the Rust & Rainbow project for details." with title "Rust & Rainbow: Post may have failed" sound name "Basso"'
fi
