# Contributing

Issues and PRs welcome. Code is ~500 LOC, **stdlib only**, readable in an afternoon.

## Setup

1. Fork + clone
2. Edit `scripts/compact.py`
3. Test with real JSONLs from `~/.claude/projects/-Users-<username>-.../*.jsonl`
4. Use `--dry-run` to keep your clipboard clean while iterating
5. Exercise all modes (`conservative`, `aggressive`, `auto`, `--raw`)
6. PRs with **adversarial tests** very welcome

## Philosophy constraints

- **Determinism, no LLM.** If a feature needs an API, it must be opt-in and well-justified.
- **stdlib only.** No `pip install`.
- **Boring Python.** No needless classes, no metaprogramming.

## Repo layout

```
claude-compact-manual/
├── README.md
├── SKILL.md                   # skill frontmatter + docs
├── scripts/
│   └── compact.py             # ~500 LOC, stdlib only
├── docs/
│   ├── usage.md
│   ├── benchmarks.md
│   ├── philosophy.md
│   ├── internals.md
│   ├── faq.md
│   └── images/
├── LICENSE
└── .gitignore
```

## Credits

- Idea: Mario Hernández (manual Sublime Text workflow crying out for automation)
- Implementation: Claude Code v2.1+, parallel agent pools
- QA: 9 agents × 2 rounds caught ~20 bugs pre-release

## Disclaimer

Personal tool made public. macOS + Claude Code v2.x. If the JSONL schema changes, the script may break. No guarantees.

## License

MIT. See [LICENSE](../LICENSE).
