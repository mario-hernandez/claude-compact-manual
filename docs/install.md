# Install

## Requirements

- macOS (tested on Sonoma and Sequoia)
- Claude Code installed and working
- Python 3.8+ (ships with modern macOS)

No `pip install`, no `npm install`, no API keys, no config file.

## Step-by-step

```bash
# 1. Clone
git clone https://github.com/mario-hernandez/claude-compact-manual.git
cd claude-compact-manual

# 2. Install the skill
mkdir -p ~/.claude/skills/compact-manual/scripts
cp SKILL.md ~/.claude/skills/compact-manual/
cp scripts/compact.py ~/.claude/skills/compact-manual/scripts/
chmod +x ~/.claude/skills/compact-manual/scripts/compact.py

# 3. Restart Claude Code if it was open
# 4. Type /compact-manual in any session
```

## First run

Type `/compact-manual` in any long session. You will see:

```
/compact-manual (conservative)   <session-uuid>.jsonl
─────────────────────────────────────────────────────────────
Original:     1,268,565 bytes  (~422,855 tokens)
Compressed:     110,246 chars  (~ 36,748 tokens)
Ratio:              8.7%        →   saved ~386,106 tokens
Turns:               41   (user 12 / assistant 29)
Tools:       Agent×33, Edit×14, Bash×11, ...

✓ Copied to clipboard (110,246 chars)
```

## The 3 steps that follow

1. `/clear` — a new session with a clean JSONL. **Not `ESC ESC`**: that is file rewind, not conversation rewind.
2. `Cmd+V` — paste the compressed transcript.
3. `Enter` — send it.

Claude resumes with the full thread, minus the dead weight of giant tool_results, base64 screenshots, and 20,000-line logs.

## When to use it

- The CLI warns `context used: >70%`
- Claude starts forgetting details from early in the session
- A debugging session has ballooned with failed builds, huge greps, test output

If you are thinking "I wish I could keep going without losing what we have done so far" — that is the moment.
