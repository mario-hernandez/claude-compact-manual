# Internals

## Algorithm behavior

**Active-session detection.** Three chained strategies:
1. Map `cwd()` to `~/.claude/projects/<encoded>/` (`/` → `-`)
2. Fall back to globally most-recent `.jsonl` by `mtime`
3. If ≥2 JSONLs modified within 15 min, stderr-warn + pick newest (use `--session` to disambiguate)

**Tail-line skip.** If last JSONL line written <2 seconds ago, drop it — avoids mid-flush JSON. Skipped for single-line files.

**Per-tool truncation.**

| Tool | Strategy |
|------|----------|
| `Bash` | head 20 + tail 10, `⋯N lines omitted` marker |
| `Grep` | head_only (already filtered) |
| `Write` / `Edit` | synthetic diff summary |
| `Read` | `summary_long` if >3 KB (`N total lines, first 5 shown`) |

**Error preservation.** Regex over tool_result content for `Traceback`, `FAIL`, `panic`, `ERROR:`. Capture ±3 lines. If the error lands in the head+tail dropped middle, re-injected at end with `[errors preserved]`.

**Dedup.** Composite key `(tool_name, key_path)` + SHA1-12 of normalized content. Identical `Read`s collapse to the first; rest become `[same as previous Read of X · unchanged]`.

**Post-compress.** UUIDs → 8 chars, `<usage>…</usage>` removed, `agentId:` prefixes stripped, Unicode subs (`⋯N`, `∅`, `⚠`).

## Edge cases

- Single-line JSONL → skip `skip_tail` (would empty the file)
- Gzip detected by magic bytes (`1f 8b`) → clean error
- `PermissionError` → friendly message
- Document blocks (base64 PDFs) → `[document: application/pdf]`
- Invalid Unicode surrogates → `errors='replace'` before `pbcopy`
- Readonly `BACKUPS_DIR` → stderr warn, continues
- Ambiguous multi-session → warn + candidate list

## Weird flag combos

- `--raw --no-dedupe` — zero transformations, forensics mode
- `--dry-run --session <old-uuid>` — audit old session without clipboard
- `aggressive --preserve-code` — low ratio, no code loss

## Conceptual pipeline

```
Session JSONL
~/.claude/projects/ ──→ find_current_session  ──→ active JSONL path
                    ──→ iter_messages         ──→ message generator (skip noise)
                    ──→ build_transcript      ──→ per-tool truncate + dedup
                    ──→ post_compress         ──→ UUID collapse, unicode subs
                    ──→ pbcopy + backup       ──→ .md + clipboard-pre-*.txt
```

## Key functions

| Function | Responsibility | LOC |
|----------|----------------|-----|
| `current_project_dir` | Encode cwd as `-Users-...-xxx` | 5 |
| `find_current_session` | Detect active JSONL + multi-session warn | 15 |
| `iter_messages` | JSONL generator + skip_tail + SKIP_TYPES | 20 |
| `clean_wrappers` | Strip harness tags | 5 |
| `post_compress` | UUID truncate, unicode subs | 10 |
| `truncate_lines` | head+tail with regex-preserved errors | 25 |
| `format_tool_use` | Render `[Read /path]`, `$ bash`, etc. | 30 |
| `format_tool_result` | Apply strategy (summary/head/head_tail) | 35 |
| `stringify_result_content` | Handle str/list/dict/image/document | 25 |
| `should_dedupe` | Decide if Bash is time-sensitive | 8 |
| `build_transcript` | Main loop + state | 75 |
| `rotate_backups` | Keep last 20 | 10 |
| `backup_clipboard` | `pbpaste` → timestamped file | 12 |
| `main` | CLI, orchestration, stats, output | 110 |

## Design decisions

- **stdlib only** — no `pip`. `argparse`, `hashlib`, `json`, `re`, `subprocess`, `pathlib`, `datetime`.
- **Markdown transcript > JSON/YAML** — JSON adds +10% tokens in boilerplate (measured).
- **Python > bash** — structured JSONL + large strings + `pbcopy` → Python wins on clarity.
- **Dedup by key-path, not line-hash** — detects "same Read unchanged" without false positives.
- **Regex-preserved errors** — cheap, deterministic, no critical false negatives.

## Code philosophy

"Boring Python". No needless classes, no metaprogramming. Short functions, clear variables, happy path first. ~500 LOC. No formal tests (personal use), but every function is testable.
