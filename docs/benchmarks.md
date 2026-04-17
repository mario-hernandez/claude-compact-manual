# Benchmarks

Measured on M2 Pro, Python 3.12, production sessions.

## Compression by session size

| Size | Turns | Tools | conservative | aggressive | --raw | Notes |
|------|-------|-------|--------------|------------|-------|-------|
| 61 MB | 69 | 131 | — | ~8% | — | chrome-devtools dump, 160 ms |
| 27 MB | 773 | 671 | ~6% | ~4% | — | Long dev session |
| 6.4 MB | 217 | 283 | 4.5% | 4.2% | 9.5% | Heavy debugging |
| 8.1 MB | 356 | 348 | ~8% | ~5% | — | Lots of Read/Edit |
| 1.5 MB | 44 | 116 | 9.1% | 7.9% | — | Skill dev |
| 1.1 MB | 31 | 61 | ~8% | — | — | Normal session |
| <80 KB | — | — | skip | skip | skip | Auto skips |

Bigger = better ratio (more duplicate tool_results to dedupe).

## Performance

| Input | Total | Peak RSS | Python peak |
|-------|-------|----------|-------------|
| 1 MB | ~50 ms | 23 MB | 0.6 MB |
| 10 MB | ~100 ms | 40 MB | 4 MB |
| 50 MB | ~150 ms | 100 MB | 20 MB |
| 100 MB | ~300 ms (projected) | ~200 MB | — |

Near-linear. 60 MB sessions in <200 ms.

## Weight breakdown

| Category | % weight | Strategy |
|----------|----------|----------|
| Tool results (Read, Bash, Grep, Agent) | **85%** | Head+tail truncate |
| User prompts | 3% | Verbatim |
| Assistant text | 7% | Verbatim |
| Thinking blocks | 2% | Discard |
| Metadata (file-history, progress) | 3% | Discard |

## Tokenization

Claude BPE averages **~3 chars/token** on technical transcripts. Stats use 3.

- 6.4 MB session ≈ 2.1 M tokens → 289 KB ≈ 96 k tokens → **saves ~2 M tokens**

## Preserved 100%

On a real 6.4 MB session:

- User prompts: 100% verbatim
- Assistant text: 100% verbatim
- Bash commands ≤500 chars (>500 → `…`)
- Errors (`Traceback`, `FAIL`, `BUILD FAILED`, etc.) + 3 context lines: 100%

## What gets lost

- Read >3 KB (conservative) or >800 B (aggressive) → first 5 lines
- Bash output >2.5 KB → head 20 + tail 10 + errors
- Agent/Task reports >3.5 KB → head 20 + tail 10 (middle lost)
- Full UUIDs → first 8 chars + `…`
- `<usage>` blocks from agents
- Consecutive duplicate tool_results → `[same as previous...]`

## Honest limitations

- `aggressive` drops middle context in long outputs. Use `conservative` or `--raw` if you need it.
- Binary files inside Read (images, PDFs) are aggressively truncated — algorithm is text-first.
- Ratios assume technical sessions. Prose-heavy sessions compress worse (~15–20%).
