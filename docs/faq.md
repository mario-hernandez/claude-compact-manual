# FAQ & Troubleshooting

## FAQ

**Why not just use `/compact`?**
`/compact` delegates to an LLM that summarizes arbitrarily. `compact-manual` is deterministic.

**Safe to paste into a new session?**
Yes. Claude parses `U:` / `A:` / `[Tool]` / `→` markers as literal history.

**Linux / Windows?**
No. Relies on `pbcopy` / `pbpaste` (macOS only).

**Can it lose critical info?**
Drops verbose `tool_results` (>3 KB) but preserves all dialogue and errors. Use `--raw` for zero loss.

**Run twice without pasting?**
Second run overwrites clipboard. `.md` backups persist.

**Backup location?**
`~/.claude/compact-backups/`. Last 20 kept.

**Recover a compacted session?**
Yes. Original JSONL is **never** modified. `claude --resume <session-id>`.

**Secrets redacted?**
**No**, deliberate. Secrets may be legitimate context. Use `--no-backup` if it worries you.

**Any size?**
Tested up to 61 MB. Linear, <200 ms.

**vs native `/compact`?**
Similar ratios, full control, zero cost. See `philosophy.md`.

## Troubleshooting

**`No JSONL found for current session`**
— `cwd` isn't under `~/.claude/projects/-...`. Run from where Claude Code launched, or pass `--session <path>`.

**`pbcopy failed`**
— Linux / Windows / SSH without display. Use `--dry-run` and copy manually from the `.md` backup.

**`Unexpectedly high ratio (90%+)`**
— Tiny session or already compacted. Expected. Tool doesn't manufacture compression where there's no redundancy.

**`Pasted transcript confuses Claude`**
— Being read as a new convo. Header includes a hint. If still confused, add: *"this is a digest of a prior session, treat it as history"*.

**`PermissionError` / `IsADirectoryError`**
— `--session` points at a dir or unreadable file. Caught cleanly since v1.1. `git pull`.

## Debugging tips

- `--dry-run` — stats + preview, zero side effects
- `--session <uuid>.jsonl` — process one old session
- `--raw` — full transcript when unsure what's being truncated

## Roadmap (no commitment)

- `--chunked` for >200 KB: TOC + on-demand Read chunks (−70% initial ratio)
- `--llm-summarize-old`: hybrid Haiku for old turns (~$0.02, opt-in)
- Auto-detect `CLAUDE_SESSION_ID` env var
- `--preserve-conclusions`: keep Agent report bullets/tables
- Linux / Windows via `xclip` / `clip.exe`
