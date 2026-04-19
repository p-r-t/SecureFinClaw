# CODEBASE.md

This document is a compact codebase map for agents that need to orient quickly, decide where to edit, and preserve the distinction between repository code and runtime workspace state.

## Reading Order

1. `pyproject.toml`
2. `finclaw/cli/commands.py`
3. `finclaw/agent/loop.py`
4. `finclaw/agent/context.py`
5. `finclaw/config/schema.py`
6. The specific package that owns the behavior you need to change

## Entry Points

- `python -m finclaw` routes through `finclaw/__main__.py` into the Typer app.
- `finclaw agent` runs a direct interactive or one-shot chat session.
- `finclaw gateway` starts the async multi-channel gateway, cron service, and heartbeat service.
- `finclaw onboard` creates config and runtime workspace bootstrap files.
- `finclaw status` reports config, workspace, provider, and key optional integration state.

## Core Runtime Loop

### 1. Startup

- `finclaw/cli/commands.py` loads config from `~/.finclaw/config.json`.
- Providers are created from the configured model and provider registry.
- `AgentLoop` is initialized with workspace path, model settings, tool settings, and optional cron or MCP configuration.

### 2. Context Assembly

- `finclaw/agent/context.py` builds the system prompt.
- Runtime bootstrap files are loaded from the workspace in this order: `AGENTS.md`, `SOUL.md`, `USER.md`, `TOOLS.md`.
- Long-term memory, financial profile, always-loaded skills, and the skill summary are appended after bootstrap files.

### 3. Tool Loop

- `finclaw/agent/loop.py` asks the provider for a response.
- If tool calls are returned, the loop executes them through `ToolRegistry`, appends tool results, and re-prompts.
- Iteration stops when the provider returns a final answer or `max_tool_iterations` is reached.

### 4. Delivery

- CLI prints directly.
- Chat channels send and receive through the message bus.
- Cron and heartbeat synthesize prompts and feed them back into the same direct processing path.

## Package Map

### `finclaw/agent/`

- `loop.py`: central orchestration, tool registration, and iterative reasoning.
- `context.py`: system prompt assembly from runtime files, memory, and skills.
- `memory.py`: persistent memory file access.
- `subagent.py`: helper management for spawned subagents.
- `tools/`: generic file, shell, web, messaging, cron, spawn, and MCP tools.

### `finclaw/agent/financial/`

- `intent.py`: decides which financial path a request should follow.
- `router.py`: metrics and search routing.
- `equity_valuation_router.py`: valuation-specific routing.
- `economics_router.py`: macro analysis orchestration.
- `meme_router.py`: meme coin scan and creation orchestration.
- `prediction_market_router.py`: Polymarket and Kalshi routing.
- `profile.py`, `history.py`, `cache.py`: user preferences, analysis history, and TTL cache.

### `finclaw/agent/financial_tools/`

- `yfinance_tool.py`: US and global equities.
- `akshare_tool.py`: Chinese markets.
- `economics_data_tool.py`: FRED and macro data.
- `financial_news_tool.py`: finance news collection.
- `earnings_tool.py`, `sec_edgar_tool.py`: earnings and filings utilities.
- `meme/` and `prediction_market/`: domain-specific execution modules used by the routers.

### `finclaw/channels/`

- One adapter per platform.
- `manager.py` is the high-level switchboard for enabled channels.
- Keep transport details local to adapters; do not leak provider logic into channel code.

### `finclaw/providers/`

- `base.py`: provider interface.
- `litellm_provider.py`: main provider implementation path.
- `openai_codex_provider.py`: OAuth-specific provider path.
- `registry.py`: provider registration and lookup.

### `finclaw/config/`

- `schema.py`: source of truth for config shape.
- `loader.py`: path resolution, persistence, camelCase migration, and disk IO.

### `finclaw/session/`, `finclaw/bus/`, `finclaw/cron/`, `finclaw/heartbeat/`

- Session storage, event routing, scheduled jobs, and recurring health prompts.

### `finclaw/skills/`

- Built-in skills that the runtime agent can progressively load.
- The repository `skills/README.md` explains the format and currently listed built-ins.

### `bridge/`

- Separate TypeScript Node.js service for WhatsApp connectivity.
- Build output goes to `bridge/dist/`.
- Python and TypeScript sides must stay aligned on websocket protocol and auth expectations.

## Repository Code Versus Runtime Workspace

Keep these separate when reasoning about changes:

### Repository code

- versioned implementation
- docs and packaging
- built-in skills
- bridge source

### Runtime workspace

- generated prompt files
- memory and history
- finance profile
- cached financial data
- user-created skills

If the task is about what the agent should remember or how it should behave at runtime, check whether the right fix belongs in workspace templates rather than in the repo root docs.

## Common Change Targets

### Add a new tool

1. Implement it in `finclaw/agent/tools/` or the appropriate financial tools package.
2. Register it in `AgentLoop._register_default_tools()`.
3. If users should discover it via prompt bootstrap, update the workspace template docs created by `onboard`.

### Add a new financial workflow

1. Add or extend the router under `finclaw/agent/financial/`.
2. Add the concrete data or execution implementation under `finclaw/agent/financial_tools/`.
3. Update any memory, profile, or cache behavior only if the workflow needs persistence.

### Change prompt composition

1. Update `finclaw/agent/context.py` if the composition order or loading rule changes.
2. Update `_create_workspace_templates()` in `finclaw/cli/commands.py` if a bootstrap file's default content changes.

### Add a new channel

1. Add config schema.
2. Add channel adapter.
3. Wire it into the channel manager.
4. Verify gateway startup still works when the channel is disabled.

## Validation Matrix

- Docs-only changes: inspect markdown links and headings.
- Python changes: `ruff check finclaw`.
- CLI path changes: `python -m finclaw --version`, `finclaw status`, and a focused command smoke test.
- Bridge changes: `npm run build` in `bridge/`.

## Current Gaps

- There is no committed `tests/` directory even though pytest is configured in `pyproject.toml`.
- Much of the operational setup is concentrated in `finclaw/cli/commands.py`, so changes there require extra care.
- Some README structure summaries are intentionally simplified; treat source files as the final authority.
