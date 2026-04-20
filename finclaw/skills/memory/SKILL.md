---
name: memory
description: >
  Two-layer persistent memory system. Use this skill to: save important facts or preferences
  the user states ("I prefer X", "my watchlist is Y"), recall past conversations or decisions
  ("what did we decide about Z last week?"), search specific past events by keyword, or update
  project context. Always active — memory is automatically managed, but the agent can read/write
  it directly when the user explicitly asks to remember or recall something.
always: true
---

# Memory

## Structure

- `memory/MEMORY.md` — **Long-term facts**: preferences, project context, relationships, watchlists.
  Loaded into every prompt. Keep it concise — only facts that matter across sessions.
- `memory/HISTORY.md` — **Append-only event log**. NOT loaded into context. Search with `grep`.
- `memory/FINANCIAL_HISTORY.md` — Financial analysis log (analyses, valuations, price checks).

## Recall Past Events

```bash
# Single keyword
grep -i "AAPL" memory/HISTORY.md

# Multiple keywords (OR)
grep -iE "meeting|deadline|budget" memory/HISTORY.md

# Specific date range
grep "2026-03" memory/HISTORY.md
```

Use the `exec` tool to run grep. Return relevant excerpts verbatim — don't paraphrase logged entries.

## Save to MEMORY.md

Write important facts **immediately** using `edit_file` or `write_file`:
- User preferences (`"prefers dark mode"`, `"risk-averse investor"`)
- Project context (`"the portfolio focuses on small-cap value"`)
- Watchlists and holdings (`"current watchlist: AAPL, BRK.B, KO"`)
- Key decisions made in conversation

**Do not save ephemeral facts** (today's prices, temporary questions). Only save facts that will
still be useful in a future session.

## When the User Asks to "Remember" Something

1. Add the fact to `MEMORY.md` under an appropriate heading.
2. Confirm: `"Got it — I've saved that to your memory."`

## When the User Asks to "Recall" or "What Did We Discuss"

1. Run `grep` on both `MEMORY.md` and `HISTORY.md`.
2. Synthesize a coherent answer from the results.
3. If nothing found, say so clearly — don't hallucinate.

## Auto-consolidation

Old conversations are automatically summarized and appended to `HISTORY.md` when sessions grow
large. Long-term facts are extracted to `MEMORY.md`. You don't need to manage this manually.
