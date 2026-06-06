#!/bin/bash
# run_welra_assessment.sh — Weekly Welra assessment, fired every Sunday at 9am via launchd.
#
# Uses the Claude Code CLI to run a fully autonomous assessment session that:
#   1. Reads R&R and Welra state from the vault
#   2. Compares R&R agent.py capabilities against the Welra build
#   3. Checks whether the Monday report ran this week
#   4. Identifies gaps and implements fixes in both codebases
#   5. Updates the vault (State, Tasks, Worklog, To_Antigravity)
#
# Output is logged to welra_assessment.log in the project directory.

LOG="/Users/ryannortham/Claude/Projects/side business/Rust & Rainbow/welra_assessment.log"
VAULT="/Users/ryannortham/MyVault"
RR_DIR="/Users/ryannortham/Claude/Projects/side business/Rust & Rainbow"
WELRA_DIR="/Users/ryannortham/Claude/Projects/side business/Welra"

# Homebrew PATH — required for claude CLI
export PATH="/Users/ryannortham/.npm-global/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:$PATH"

echo "---" >> "$LOG"
echo "$(date '+%Y-%m-%d %H:%M:%S') — starting Welra weekly assessment" >> "$LOG"

/Users/ryannortham/.npm-global/bin/claude --print --dangerously-skip-permissions "
You are running the weekly Welra / Rust & Rainbow assessment. Today is $(date '+%Y-%m-%d') (Sunday). Work autonomously — read, assess, implement, then document. Do not ask questions.

## Context
- Vault root: $VAULT
- R&R project: $RR_DIR
- Welra project: $WELRA_DIR

## Your tasks, in order:

### 1. Read current state
Read these files to orient yourself:
- $VAULT/Projects/Rust_and_Rainbow/State.md
- $VAULT/Projects/AutoBiz/State.md
- $VAULT/Projects/Rust_and_Rainbow/Tasks.md
- $VAULT/Projects/AutoBiz/Tasks.md
- $VAULT/memory/Learnings_and_Conventions.md

### 2. Check this week's R&R report
- List files in $RR_DIR/reports/ and read the most recent one
- Check if a report was generated this week (Monday $(date -v-6d '+%Y-%m-%d') to today)
- If no report exists for this week, note it as a gap

### 3. Assess R&R vs Welra
Read $RR_DIR/agent.py (focus on --mode market, --mode report, hashtag logic, TikTok/Instagram posting).
Read the Welra integrations in $WELRA_DIR/apps/api/src/integrations/ and $WELRA_DIR/apps/api/src/services/reportGenerator.ts.
Compare what R&R does against what Welra supports. Look for:
  - New integrations in Welra that R&R should learn from
  - Learnings from R&R operations that Welra's code should incorporate
  - Bugs, stale config, or improvements in either codebase
  - Any posts that were missed this week (check $RR_DIR/market.log)

### 4. Implement fixes
For any concrete gap or bug you find, implement the fix directly. Edit the relevant files.
Do not leave TODOs — either fix it or add it to the vault Tasks.md with [owner:: ryan] if it requires Ryan.

### 5. Update the vault
Update these files with today's date and a summary of what you found and changed:
- $VAULT/Projects/Rust_and_Rainbow/State.md — update 'updated:' frontmatter, note any status changes
- $VAULT/Projects/AutoBiz/State.md — update 'updated:' frontmatter, note any Welra build progress
- $VAULT/Projects/Rust_and_Rainbow/Tasks.md — check off completed items, add new ones
- $VAULT/Worklogs/Claude_Log.md — prepend a new entry: '## $(date '+%Y-%m-%d') (Sunday Assessment)' with bullet points of everything assessed and changed
- $VAULT/_Inbox/To_Antigravity.md — prepend a new section summarising the assessment for Antigravity

All vault notes must have YAML frontmatter with updated: $(date '+%Y-%m-%d').
All new tasks must use: - [ ] Description [owner:: ryan|claude] [priority:: high|medium|low] [status:: open]
" >> "$LOG" 2>&1

EXIT_CODE=$?
echo "$(date '+%Y-%m-%d %H:%M:%S') — assessment complete (exit $EXIT_CODE)" >> "$LOG"

# Fire a macOS notification with the result
if [ $EXIT_CODE -eq 0 ]; then
    osascript -e 'display notification "Check welra_assessment.log for details." with title "Welra Assessment: Complete ✓" sound name "Glass"'
else
    osascript -e 'display notification "Check welra_assessment.log — something went wrong." with title "Welra Assessment: Failed ✗" sound name "Basso"'
fi
