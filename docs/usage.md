# Usage

## Modes

| Mode | When | Ratio | Loss |
|------|------|-------|------|
| `conservative` (default) | 300 KB – 1.5 MB sessions | ~10% | Truncates large `tool_results` |
| `aggressive` | Critical sessions >1.5 MB | ~4–5% | Truncates `tool_results` harder |
| `auto` | Unknown size | Adaptive | Picks mode by JSONL weight |
| `--raw` | Full fidelity | ~10–15% | Only strips harness noise |
| `--preserve-code` | Heavy code editing | +80% vs conservative | Never truncates Read/Edit/Write |

## Flags

- `conservative` — default, balanced
- `aggressive` — max compression
- `auto` — size-adaptive
- `--raw` — strips only harness wrappers
- `--preserve-code` — never truncates Read/Edit/Write
- `--dry-run` — compute + print, no clipboard, no backup
- `--session <path>` — process a specific JSONL
- `--no-backup` — skip `~/.claude/compact-backups/`
- `--no-clipboard-backup` — skip saving prior clipboard
- `--no-dedupe` — disable consecutive tool_call dedup

## Examples

```bash
/compact-manual                              # default conservative
/compact-manual aggressive                   # large session
/compact-manual --raw                        # max fidelity
/compact-manual aggressive --preserve-code   # compress but keep code intact
/compact-manual --dry-run                    # preview only
/compact-manual --session /path/to/old.jsonl # compact an old session
/compact-manual auto --preserve-code --no-backup
```

## The 3-step workflow after running

1. `/clear` — new session (do NOT use `ESC ESC`, that's file rewind)
2. `Cmd+V` — paste the clipboard transcript
3. `Enter` — send

## Preserved vs truncated

| Category | Treatment |
|----------|-----------|
| User prompts, assistant text, errors (Traceback/FAIL/stack traces) | Verbatim |
| Read >3 KB, Bash >2.5 KB, Agent reports >3.5 KB | Head+tail with `[... N lines omitted ...]` |
| `thinking` blocks, `file-history-snapshots`, harness `system-reminders`, UUIDs | Discarded / shortened |

`--raw` mode only applies the third row.

## Backups

Every run (unless `--no-backup`) writes:

- `~/.claude/compact-backups/YYYYMMDD-HHMMSS-xxxx-{mode}.md` — the digest (last 20 kept)
- `~/.claude/compact-backups/clipboard-pre-YYYYMMDD-HHMMSS.txt` — prior clipboard

Restore:

```bash
ls -lt ~/.claude/compact-backups/ | head -20
cat ~/.claude/compact-backups/20260416-143022-a3f9-conservative.md | pbcopy
```

## When to run

- CLI warns `context used: >70%`
- Claude forgets early session details
- Debugging session ballooned with failed builds / greps / logs
