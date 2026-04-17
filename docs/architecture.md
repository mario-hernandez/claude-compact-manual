# Architecture

The script is ~500 LOC, deliberately plain, stdlib only.

## Repo structure

```
claude-compact-manual/
├── README.md                  # manifesto
├── SKILL.md                   # frontmatter + skill documentation
├── scripts/
│   └── compact.py             # main logic (~500 LOC, stdlib only)
├── docs/
│   ├── install.md
│   ├── usage.md
│   ├── benchmarks.md
│   ├── architecture.md
│   ├── philosophy.md
│   ├── power-user.md
│   ├── faq.md
│   └── images/
├── LICENSE                    # MIT
└── .gitignore
```

No `requirements.txt`, no `setup.py`, no `pyproject.toml`. Single executable file, Python 3.8+ that macOS ships by default.

## Pipeline

```
Session JSONL           ┌─────────────────────┐
~/.claude/projects/ ──→ │ find_current_session│ ──→ active JSONL
                        └─────────────────────┘
                                   ↓
                        ┌─────────────────────┐
                        │   iter_messages()   │ ──→ message generator (skip noise)
                        └─────────────────────┘
                                   ↓
                        ┌─────────────────────┐
                        │  build_transcript() │ ──→ per-tool truncate + dedup
                        └─────────────────────┘
                                   ↓
                        ┌─────────────────────┐
                        │   post_compress()   │ ──→ UUID collapse, unicode subs
                        └─────────────────────┘
                                   ↓
                        ┌────────┐   ┌────────┐
                        │ pbcopy │   │ backup │ ──→ .md + clipboard-pre-*.txt
                        └────────┘   └────────┘
```

## Key functions

| Function | Responsibility | LOC |
|---|---|---|
| `current_project_dir()` | Encodes cwd as `-Users-<username>-...-xxx` | 5 |
| `find_current_session()` | Detects active JSONL + multi-session warn | 15 |
| `iter_messages()` | JSONL generator with skip_tail + SKIP_TYPES | 20 |
| `clean_wrappers()` | Strip harness tags | 5 |
| `post_compress()` | UUID truncate, unicode subs | 10 |
| `truncate_lines()` | head+tail with regex-preserved errors | 25 |
| `format_tool_use()` | Renders `[Read /path]`, `$ bash`, etc | 30 |
| `format_tool_result()` | Applies strategy (summary/head/head_tail) | 35 |
| `stringify_result_content()` | Handles str/list/dict/image/document | 25 |
| `should_dedupe()` | Decides if Bash is time-sensitive | 8 |
| `build_transcript()` | Main loop + state | 75 |
| `rotate_backups()` | Keeps last 20 | 10 |
| `backup_clipboard()` | pbpaste → timestamped file | 12 |
| `main()` | CLI, orchestration, stats, output | 110 |

## Design decisions

- **stdlib only**: `argparse`, `hashlib`, `json`, `re`, `subprocess`, `pathlib`, `datetime`.
- **Markdown transcript > JSON/YAML**: measured, JSON adds +10% tokens in boilerplate.
- **Python > bash**: structured JSONL + large strings + `pbcopy` = Python wins on clarity.
- **Dedup by key-path, not line-hash**: detects "same Read unchanged" without false positives.
- **Regex-preserved errors**: cheap, deterministic, no critical false negatives.

## Contributing

1. Fork and clone.
2. Change `scripts/compact.py`.
3. Test with real JSONLs from `~/.claude/projects/-Users-<username>-.../*.jsonl`.
4. Run with `--dry-run`.
5. Try the modes.
6. Adversarial tests welcome.

## Code philosophy

Boring Python. No classes for their own sake, no metaprogramming. Short functions, clear variables, happy path first. When "elegant" fights "obvious," obvious wins. 450 LOC is enough.
