# FinClaw Skills

Built-in skills that extend FinClaw's capabilities. Skills are loaded into context when triggered
by the user's request, based on the `description` field in each `SKILL.md`.

## Skill Format

Each skill is a directory containing a `SKILL.md` file with:
- YAML frontmatter (`name`, `description`, optional `always: true`)
- Markdown instructions loaded into context when the skill triggers

## Available Skills

| Skill | Emoji | Description |
|-------|-------|-------------|
| `cron` | ⏰ | Schedule recurring tasks and reminders |
| `earnings` | 📅 | Earnings dates, beat/miss history, analyst consensus estimates |
| `github` | 🐙 | Interact with GitHub via the `gh` CLI (PRs, issues, CI runs) |
| `investment-critic` | 🔴 | Adversarially red-team an investment thesis; find value traps and bear cases |
| `meme-create` | 🪙 | Deploy meme coins on pump.fun (Solana) |
| `memory` | 🧠 | Two-layer persistent memory with grep-based recall |
| `odds-chart` | 📈 | Plot Polymarket prediction market probability charts |
| `skill-creator` | 🛠️ | Create and package new skills |
| `stock-screener` | 🔍 | Screen a universe of stocks for value investing ideas; generate a watchlist |
| `summarize` | 🧾 | Summarize URLs, files, and YouTube videos |
| `tmux` | 🧵 | Remote-control tmux sessions for interactive CLIs |
| `value-investing` | 💰 | Pabrai "Dhandho" deep analysis and DCF valuation for a specific ticker |
| `weather` | 🌤️ | Current weather and forecasts (no API key required) |

## Value Investing Workflow

The three value investing skills form a deliberate pipeline:

```
stock-screener  ──→  value-investing  ──→  investment-critic
  "Find ideas"       "Build the case"      "Tear it apart"
   Discovery            Analysis           Adversarial Review
```

1. **`stock-screener`** — Scans Superinvestor 13F filings + sector universes to surface candidates
2. **`value-investing`** — Runs a full Dhandho analysis (fundamentals, qualitative, DCF) on a ticker
3. **`investment-critic`** — Red-teams the thesis, identifies value traps, sets kill criteria

Use all three in sequence for a rigorous investment review. Use `value-investing` alone for a
quick analysis when you already have a ticker.

## Attribution

Skills adapted from [OpenClaw](https://github.com/openclaw/openclaw)'s skill system.
The format and metadata structure follow OpenClaw conventions for compatibility.