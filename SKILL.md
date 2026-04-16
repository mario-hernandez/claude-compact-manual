---
name: compact-manual
description: "Claude Code skill for deterministic context compaction. Compresses the current Claude Code session to the clipboard for a manual rewind+paste workflow. A deterministic alternative to /compact that extracts literal dialog and truncates only tool outputs — no LLM summarization. Use when the user says 'compact the session', 'compact-manual', 'clean the context', or invokes /compact-manual."
argument-hint: "[conservative|aggressive|auto|--raw] [--preserve-code] [--dry-run] [--no-dedupe]"
allowed-tools: Bash
metadata:
  author: mario-hernandez
  version: 1.1
---

## What it does

Reads the current session's JSONL (auto-detects the project directory in `~/.claude/projects/`, picks the most recent file), extracts the user/assistant dialog, truncates verbose tool_results (with regex-based preservation of full errors), formats it as a markdown transcript, copies it to the clipboard with `pbcopy`, and saves a backup in `~/.claude/compact-backups/`.

The user then runs **`/clear`** (creates a fresh session with a clean JSONL — the previous one is archived) and pastes with `Cmd+V` to start over with the compressed transcript as the sole context.

## How to run it

Execute the script with Bash, **passing the user's arguments via `$ARGUMENTS`**:

```bash
python3 ~/.claude/skills/compact-manual/scripts/compact.py $ARGUMENTS
```

If the user passed no args, `$ARGUMENTS` is empty and the script runs in `conservative` mode by default.

### Arguments

| Arg | Effect |
|-----|--------|
| (none) | **Conservative** mode (default). Truncates tool_results >2-3KB, keeps dialog literal |
| `aggressive` | Truncates tool_results very short (~600 chars), ideal for sessions >1.5MB |
| `auto` | Picks `aggressive` if session >1.5MB, `conservative` if <1.5MB, skips if <80KB |
| `--raw` | **Ultra-literal mode**: no truncation, no dedup, no post_compress. Only strips harness wrappers (`<system-reminder>`, etc). Ratio ~9-15% but full fidelity. Use it when you want to preserve EVERYTHING without automatic decisions |
| `--preserve-code` | Never aggressively truncates Read/Edit/Write (multiplies their limits by 8) |
| `--no-dedupe` | Disables dedup of identical tool_results |
| `--dry-run` | Preview + stats without copying or saving backup |
| `--session <path>` | Processes a specific JSONL (default: most recent in current project) |
| `--no-backup` | Does not save backup (normally saves, retains last 20) |
| `--no-clipboard-backup` | Does not save the previous clipboard before overwriting |

### Invocation examples

```bash
python3 ~/.claude/skills/compact-manual/scripts/compact.py                # default: conservative
python3 ~/.claude/skills/compact-manual/scripts/compact.py aggressive
python3 ~/.claude/skills/compact-manual/scripts/compact.py auto
python3 ~/.claude/skills/compact-manual/scripts/compact.py --raw           # ultra-fidelity
python3 ~/.claude/skills/compact-manual/scripts/compact.py --dry-run
python3 ~/.claude/skills/compact-manual/scripts/compact.py aggressive --preserve-code
```

## What to report to the user afterwards

1. **Compression ratio** (original/compressed, estimated tokens saved)
2. **Path of the saved backup**
3. **Confirmation** that it is on the clipboard
4. **Clear final instructions**:
   - `/clear` (creates a fresh session with a clean JSONL — the current one stays accessible via `/resume`)
   - `Cmd+V` to paste the transcript
   - Enter to send

Important: **do NOT suggest ESC ESC** — in Claude Code that is a rewind of file edits (file checkpoints), NOT a conversation rewind. The correct way to start with a clean context is `/clear`.

## Design principles

- **Does not use an LLM to compress** → deterministic, no arbitrary loss. You choose what to drop.
- **Preserves literal dialog** (user + assistant text) → the narrative fabric stays intact.
- **Only truncates tool_results** (where 85% of the weight lives according to empirical analysis).
- **Preserves full errors** (regex matches in Bash/Task with ±3 lines of context).
- **Automatic backup** in `~/.claude/compact-backups/` (retains last 20).
- **Observed ratios**: 4-5% on large sessions (>1MB), 10-15% on medium sessions.

## Full flow (to guide the user)

```
1. /compact-manual       ← skill processes JSONL, transcript to clipboard + backup
2. /clear                ← new session with clean JSONL (previous archived in /resume)
3. Cmd+V                 ← paste the compressed transcript
4. Enter                 ← send, keep working with the compressed context
```

**Why `/clear` and not ESC ESC**: in Claude Code, ESC ESC reverts _file edits_ (local checkpoints), not the conversation. `/clear` does create a completely new session with its own JSONL, which is what we want so that the next `/compact-manual` does not reprocess the old conversation redundantly.
