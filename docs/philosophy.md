# Philosophy

## Why not native `/compact`

Native `/compact` delegates to an LLM. The model decides what "isn't important" and throws it away — arbitrary heuristics, opaque decisions, tokens spent on summarizing your own session. You can't audit what was dropped. The specific stack trace or variable value you needed ten turns later is gone.

## compact-manual principles

- **Determinism** — same JSONL → same output. If something disappears, you trace which rule killed it.
- **Dialogue fidelity** — user prompts literal, assistant text verbatim. Nothing interpreted.
- **Honest about loss** — explicit markers: `[45 lines omitted]`, `[same as previous Read of X]`.
- **Explicit trade-off** — `--raw` for zero loss, `aggressive` for minimum ratio. Your call.

## Side-by-side

| Aspect | Native `/compact` | `compact-manual` |
|--------|-------------------|------------------|
| Engine | LLM (Claude) | Deterministic rules |
| Cost | Tokens (input + output) | Free, local |
| Speed | Depends on API latency | <200 ms always |
| Dialogue fidelity | Interpreted | Literal |
| Auditable | No | Yes (readable Python) |
| Control | One mode | 4 modes + 6 flags |
| Ratio | Variable | 4–15% by mode |
| Privacy | Ships to Anthropic | 100% local |
| Deps | Claude Code + API | Claude Code + stdlib |

## When native `/compact` wins

- You want a **narrative summary** for a human to read
- You don't care about technical detail, just the arc
- Purely conversational session, few tool_uses

## When `compact-manual` wins

- Coding / debugging sessions with lots of tool output
- Long iterations on the same file (dedup shines)
- You need the narrative thread without paraphrase
- You want predictable ratio + cost
- You want to audit what was dropped

## Real anecdote

217-turn debugging session, 283 tool_uses, 6.4 MB. `aggressive` compressed to 274 KB (4.2%). 85% of weight was `tool_results` from Read and Bash. Preserved 54 user prompts + 163 assistant texts verbatim. Native `/compact` would have produced ~2,000 narrative words — useful for a human recap, useless for resuming at the exact debug point.
