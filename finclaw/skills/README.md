# FinClaw Skills

Built-in skills that extend FinClaw's capabilities. Skills are loaded into context when triggered
by the user's request, based on the `description` field in each `SKILL.md`.

## Skill Format

Since FinClaw uses a plugin-style grouping, skills are stored in subdirectories corresponding to their domain (e.g., `investing/`, `tools/`). A skill is a directory containing a `SKILL.md` file with:
- YAML frontmatter (`name`, `description`, optional `always: true`)
- Markdown instructions loaded into context when the skill triggers

## Available Skills

### Investing & Finance Pipeline
| Skill | Emoji | Description |
|-------|-------|-------------|
| `bet-sizing` | 📏 | Kelly criterion, position sizing, and maximum drawdown calculations |
| `earnings` | 📅 | Earnings dates, beat/miss history, analyst consensus estimates |
| `historical-risk` | 📉 | Quantify risk (volatility, max drawdown, historical VaR) |
| `investment-critic` | 🔴 | Adversarially red-team an investment thesis; find value traps and bear cases |
| `market-regime` | 🌍 | Classify macro regime (Bull/Bear) using SPY & sector breadth. Instructs MoS to use. |
| `qualitative-valuation` | 🏰 | Assess business moats, Five Forces, and management quality |
| `stock-screener` | 🔍 | Screen a universe of stocks for value investing ideas; generate a watchlist |
| `value-investing` | 💰 | Pabrai "Dhandho" deep analysis and DCF valuation for a specific ticker |


### Tools
| Skill | Emoji | Description |
|-------|-------|-------------|
| `github` | 🐙 | Interact with GitHub via the `gh` CLI (PRs, issues, CI runs) |
| `memory` | 🧠 | Two-layer persistent memory with grep-based recall |
| `tmux` | 🧵 | Remote-control tmux sessions for interactive CLIs |

### Fun
| Skill | Emoji | Description |
|-------|-------|-------------|
| `meme-create` | 🪙 | Deploy meme coins on pump.fun (Solana) |
| `odds-chart` | 📈 | Plot Polymarket prediction market probability charts |
| `weather` | 🌤️ | Current weather and forecasts (no API key required) |

### Core System
| Skill | Emoji | Description |
|-------|-------|-------------|
| `cron` | ⏰ | Schedule recurring tasks and reminders |
| `skill-creator` | 🛠️ | Create and package new skills |
| `summarize` | 🧾 | Summarize URLs, files, and YouTube videos |

## Value Investing Workflow

The value investing skills form a deliberate pipeline:

```
 market-regime → stock-screener → value-investing → investment-critic → bet-sizing
"Set Context"     "Find ideas"    "Build the case"   "Tear it apart"    "Size the bet"
```

Supporting skills feed into the pipeline at specific stages:
- **`qualitative-valuation`** → Stage 2 of `value-investing` (moat assessment framework)
- **`historical-risk`** → `investment-critic` (quantitative risk data)
- **`earnings`** → `stock-screener` + `value-investing` (forward estimates, revision trends)

Use all of them in sequence for a rigorous investment review. Use `value-investing` alone for a
quick analysis when you already have a ticker.

## Progressive Disclosure

To minimize the "base load" of our LLM context window, larger skills implement **Progressive Disclosure**:
- The core `SKILL.md` holds the operational checklist, trigger criteria, and rules of engagement (typically < 4K characters).
- Heavy, deep-dive reference material (e.g. complex formulas, mathematical worked examples) are sequestered into `references/detail.md` inside the skill directory.
- The agent is instructed to read the reference markdown file using `read_file` ONLY if it needs a refresher on the math.

## Attribution

Skills adapted from [OpenClaw](https://github.com/openclaw/openclaw)'s skill system and [finance_skills](https://github.com/JoelLewis/finance_skills).
The format and metadata structure follow OpenClaw conventions for compatibility.