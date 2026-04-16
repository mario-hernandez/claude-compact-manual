# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2026-04-17

### Added
- `--raw` mode for ultra-literal compression (no truncation, no dedup, no post-compress — only strips harness wrappers)
- `--no-dedupe` flag to disable tool_result deduplication
- `--no-clipboard-backup` flag to skip saving previous clipboard contents
- Clipboard backup: saves `pbpaste` output to `~/.claude/compact-backups/clipboard-pre-*.txt` before overwriting
- Multi-session warning: if multiple JSONLs modified in last 15 minutes, prints candidates to stderr
- Dynamic session detection: uses `cwd()` to locate the project dir instead of hardcoded paths
- Document block handling for PDF/binary inline attachments (rendered as `[document: media_type]`)
- Gzip magic byte detection with clean error message
- `$ARGUMENTS` expansion in SKILL.md so user-passed args reach the Python script

### Fixed
- Null-safety crashes in `format_tool_use` when tool inputs have `None` values
- `IsADirectoryError` when `--session` points to a directory instead of a file
- `PermissionError` on JSONL read: now shows clean message instead of raw stacktrace
- Unicode surrogate pairs causing `pbcopy` to fail — now sanitized before clipboard
- Single-line JSONL files being treated as empty (skip-tail guard)
- User text blocks over 100KB crashing clipboard on pastes — now truncated with marker
- `BACKUPS_DIR` readonly: warns via stderr instead of crashing
- Backup filename collision when two runs happen in the same second (now includes ms)
- `ERROR_RX` false positives on "Cannot"/"denied" strings — now anchored at line start
- `NO_DEDUPE_CMDS` matching `lsof` when looking for `ls` — now requires exact match or space delimiter
- Dedup marker no longer uses unreliable turn counter; uses descriptive reference instead
- `document` block with non-dict `source` no longer crashes

### Changed
- Token ratio heuristic updated from `chars/4` to `chars/3` (empirical measurement from Claude BPE tokenizer)
- UUID collapse: full UUIDs in the transcript are now truncated to 8 chars + `…` to save tokens
- Backup rotation now also cleans `clipboard-pre-*.txt` files (retained: last 20 of each type)

### Security
- No secrets redaction (deliberate decision): secrets in transcripts are left intact because they may be legitimate context. Use `--no-backup` if concerned.

## [1.0.0] - 2026-04-16

### Added
- Initial release
- Modes: `conservative` (default), `aggressive`, `auto`
- `--preserve-code` flag to avoid aggressive truncation of Read/Edit/Write
- `--dry-run` flag for preview without writing
- `--session <path>` for processing specific JSONL files
- `--no-backup` flag
- Automatic backup to `~/.claude/compact-backups/` with rotation (last 20)
- Tool-result deduplication based on `(tool_name, key_path) + SHA1` hash
- Error preservation: regex-matched errors (Traceback, FAIL, panic, ERROR:) preserved even when truncated
- Post-compression: `<usage>` block stripping, `agentId:` line removal, Unicode substitutions (`⋯N`, `∅`, `⚠`)
- Markdown transcript format with `U:` / `A:` / `[Tool args]` / `→` conventions
