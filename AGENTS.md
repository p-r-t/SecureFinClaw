# AGENTS.md

This file is for coding agents and contributors working on the FinClaw repository.

It is not the same as the runtime `AGENTS.md` generated inside `~/.finclaw/workspace/` by `finclaw onboard`. The runtime file is part of the agent's prompt bootstrap. This repository file explains how to navigate and modify the codebase safely.

## Start Here

Read these files first when you need orientation:

1. `README.md` for product scope, user-facing setup, and high-level architecture.
2. `CODEBASE.md` for a compact map of execution flow, module ownership, and edit targets.
3. `CODE_STYLE.md` for repository-specific code and documentation style rules.
4. `pyproject.toml` for packaging, dependencies, CLI entrypoints, and dev tools.
5. `finclaw/cli/commands.py` for the operator entrypoints (`onboard`, `agent`, `gateway`, `status`).
6. `finclaw/agent/loop.py` for tool registration and the core reasoning loop.
7. `finclaw/agent/context.py` for how system prompt context is assembled.
8. `finclaw/config/schema.py` and `finclaw/config/loader.py` for config shape and on-disk key migration.

## Mental Model

FinClaw has two different working surfaces:

- Repository code under this repo: implementation, packaging, docs, built-in skills, and the WhatsApp bridge.
- Runtime workspace under `~/.finclaw/workspace`: prompt bootstrap files, memory, cached financial data, and user-defined skills.

Most bugs in agent behavior come from confusing those two layers.

## Request Flow

1. A user enters through CLI or a chat channel.
2. `finclaw/cli/commands.py` loads config, builds providers, and creates `AgentLoop`.
3. `AgentLoop` registers general tools, financial routers, optional cron support, and optional MCP servers.
4. `ContextBuilder` loads runtime bootstrap files in this order: `AGENTS.md`, `SOUL.md`, `USER.md`, `TOOLS.md`, then memory and skills.
5. The provider runs the chat completion loop with tool calling until a final answer is produced or the iteration budget is exhausted.
6. Responses are written back through the message bus to the originating channel.

## High-Signal Directories

- `finclaw/agent/`: core loop, context assembly, memory, subagents, routers, and tool abstractions.
- `finclaw/agent/financial/`: financial intent detection, profile/history/cache management, and router logic.
- `finclaw/agent/financial_tools/`: data-source integrations and domain-specific execution modules.
- `finclaw/channels/`: channel adapters for Telegram, Discord, Slack, WhatsApp, Feishu, DingTalk, Email, Mochat, and QQ.
- `finclaw/providers/`: LLM provider implementations and provider registry.
- `finclaw/config/`: pydantic schema, path resolution, and config persistence.
- `finclaw/skills/`: built-in skills loaded into runtime context.
- `bridge/`: Node.js WhatsApp bridge compiled with TypeScript.

## Edit Guide

Change the smallest surface that owns the behavior:

- New CLI behavior: edit `finclaw/cli/commands.py`.
- New runtime prompt/bootstrap behavior: edit `_create_workspace_templates()` in `finclaw/cli/commands.py` and check `finclaw/agent/context.py`.
- New financial capability: start in `finclaw/agent/financial/` and only drop into `financial_tools/` when the behavior needs a concrete data integration.
- New generic tool: add the implementation under `finclaw/agent/tools/` and register it in `AgentLoop._register_default_tools()`.
- New provider: add implementation under `finclaw/providers/` and wire it through the registry/config helpers.
- New channel: add a `channels/` adapter and then enable it through `ChannelManager` and config schema.
- New built-in skill: add `finclaw/skills/<name>/SKILL.md` and update `finclaw/skills/README.md` if the skill should be discoverable.
- WhatsApp changes: if protocol or transport behavior changes, inspect both `bridge/src/` and `finclaw/channels/whatsapp.py`.

## State And Persistence

- User config lives at `~/.finclaw/config.json`.
- Default runtime workspace lives at `~/.finclaw/workspace`.
- Long-term memory lives at `~/.finclaw/workspace/memory/MEMORY.md`.
- Searchable history lives at `~/.finclaw/workspace/memory/HISTORY.md`.
- Financial history lives at `~/.finclaw/workspace/memory/FINANCIAL_HISTORY.md`.
- Cached financial data lives under `~/.finclaw/workspace/financial_data/`.
- Cron state lives under `~/.finclaw/cron/jobs.json`.

## Validation

There is no committed `tests/` directory at the moment. Use lightweight validation that matches the touched surface:

- Python changes: `ruff check finclaw`
- Packaging/CLI smoke: `python -m finclaw --version` and `finclaw status`
- Bridge changes: in `bridge/`, run `npm install` if needed and `npm run build`
- Docs changes: verify links and file names, especially `AGENTS.md` versus runtime workspace bootstrap docs

## Sharp Edges

- Config is stored on disk in camelCase but validated in Python as snake_case. `config/loader.py` handles the conversion.
- `ContextBuilder` reads runtime files from the workspace, not from this repository root.
- `finclaw/cli/commands.py` currently owns a large amount of setup logic, including workspace template generation.
- Financial behavior is split between router modules and data-tool modules; changing one without the other often produces partial fixes.
- The README is user-facing. Keep this file and `CODEBASE.md` dense and operational; keep the README broader.
- Follow `CODE_STYLE.md` when adding or modifying Python, TypeScript bridge code, or agent-facing documentation.
