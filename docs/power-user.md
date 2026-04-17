# Power user & edge cases

Internal behavior for auditing, extending, or trusting `compact-manual` in a serious pipeline. Everything here is implemented — not roadmap.

## Advanced algorithm behavior

**Active-session detection.** Three chained strategies: map `cwd()` to `~/.claude/projects/<encoded>/` (encoding replaces `/` with `-`); fall back to the globally most-recent session by `mtime`. If two or more `.jsonl` files were modified within the last 15 minutes, a stderr warning lists the candidates, picks the newest, and tells you to verify with `--session`.

**Tail-line skip.** Before parsing, checks the JSONL's `mtime`. If the last line was written less than 2 seconds ago, it is dropped: avoids reading a JSON object mid-flush while a live session is still writing. Does not apply to single-line files.

**Per-tool truncation.**
- `Bash` → **head+tail** (first 20 lines + last 10, with `⋯N lines omitted` marker)
- `Grep` → **head_only**
- `Write` / `Edit` → **summary** (synthetic diff)
- `Read` → **summary_long** if >3 KB (`N total lines, first 5 shown`)

**Error preservation.** Regex over `tool_result` content for `Traceback`, `FAIL`, `panic`, `ERROR:`. Captures ±3 lines of context. If the error section lands in the "middle" dropped by head+tail, it is re-injected at the end with `[errors preserved]` prefix.

**Dedup.** Composite key `(tool_name, key_path) + SHA1-12` of normalized content. Two `Read`s of the same file with identical output collapse to the first; the rest become `[same as previous Read of X · unchanged]`.

**Post-compress.** Final pass: UUIDs → 8 chars, `<usage>…</usage>` removed, `agentId:` prefixes stripped, Unicode substitutions (`⋯N`, `∅` for empty output, `⚠` for warnings).

## Edge cases handled

- Single-line JSONL → `skip_tail` is skipped (would empty the file).
- Gzip files detected by magic bytes (`1f 8b`) → clean error.
- `PermissionError` → friendly message, no raw stack trace.
- Document blocks (base64-embedded PDFs) → `[document: application/pdf]` instead of a dump.
- Invalid Unicode surrogates → sanitized via `errors='replace'` before `pbcopy`.
- Readonly `BACKUPS_DIR` → stderr warning and continues; does not crash.
- Ambiguous multi-session → warning + candidate list.

## Flag combinations worth knowing

- `--raw --no-dedupe` → zero transformations. Handy for forensics.
- `--dry-run --session <old-uuid>` → audit an old session without touching the clipboard.
- `aggressive --preserve-code` → low ratio but no code loss.
