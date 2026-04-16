# Contributing to compact-manual

Thanks for your interest. This is a small personal project (~600 LOC, stdlib-only) and contributions are welcome.

## Quick ground rules

- The philosophy is **deterministic, local, no LLM**. Features that need API calls must be opt-in and well-justified.
- Keep it stdlib-only unless there's a strong reason.
- Prefer "boring Python" over clever metaprogramming.
- Short functions, clear names, happy path first.

## Before submitting a PR

1. Fork the repo and clone locally.
2. Test your changes against real JSONLs from your own `~/.claude/projects/...`.
3. Always test with `--dry-run` first to avoid touching your clipboard while iterating.
4. Run the 4 modes to make sure nothing regresses: `conservative`, `aggressive`, `auto`, `--raw`.
5. If your change affects user-facing output, update README tables/examples.

## Adversarial test ideas (welcome as PRs)

- Empty JSONL
- JSONL >100 MB
- JSONL with malformed lines mid-stream
- Messages without `role`
- Orphan tool_results (tool_use_id pointing to nothing)
- Binary content embedded (document blocks)
- Unicode edge cases (surrogates, RTL, emoji combining)

## Reporting bugs

Open an issue with:
- macOS version + Python version
- Claude Code version (`claude --version`)
- A minimal JSONL that reproduces the bug (redact sensitive content first)
- Expected vs actual behavior

## Code style

- No linter enforced. `black` and `ruff` with defaults pass clean.
- Docstrings only when WHY is non-obvious.
- No new dependencies without discussion in an issue first.

## Features on the roadmap

See [README.md](README.md#-roadmap) — if you want to tackle one, open an issue first so we can discuss approach.
