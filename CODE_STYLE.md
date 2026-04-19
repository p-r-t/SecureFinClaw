# CODE_STYLE.md

This guide is for coding agents and contributors making changes in the FinClaw repository.

It is intentionally repository-specific. When this file conflicts with generic style advice, prefer the patterns already used in this codebase.

## Primary Rules

1. Make the smallest change that fully fixes the problem.
2. Fix behavior at the owning layer instead of adding workaround logic elsewhere.
3. Preserve public command names, config keys, and runtime file names unless the task explicitly requires changing them.
4. Match existing structure before introducing a new abstraction.
5. Keep repository docs, runtime workspace templates, and generated user state clearly separated.

## Codebase Boundaries

FinClaw has two distinct surfaces:

- Repository code: versioned Python, TypeScript bridge code, packaging, built-in skills, and docs in this repo.
- Runtime workspace: files under `~/.finclaw/workspace/` created by `finclaw onboard`, including `AGENTS.md`, `SOUL.md`, `USER.md`, `TOOLS.md`, memory, and cached data.

If the task changes what the live agent sees in its prompt, update the workspace template generation in `finclaw/cli/commands.py` and verify how `finclaw/agent/context.py` loads it.

## Python Style

### General

- Target Python 3.11+ idioms already used in the repo.
- Use type hints on public functions, methods, and important local structures.
- Prefer `str | None`, `list[str]`, and `dict[str, Any]` over older `Optional`, `List`, and `Dict` spellings.
- Use descriptive names. Avoid single-letter variables outside short comprehensions.
- Keep functions focused; extract helpers only when it reduces repeated logic or isolates a clear concern.
- Follow the repo's Ruff configuration: 100-column target, import sorting, and standard lint rules from `pyproject.toml`.

### Imports

- Group imports in the existing Ruff-compatible order: stdlib, third-party, local.
- Prefer direct imports over deep aliasing.
- Keep lazy imports only when they avoid startup cost, optional dependency failures, or circular imports.

### Data Modeling

- Use `pydantic.BaseModel` for configuration and validated structured inputs.
- Use `dataclass` for simple event/message containers when validation is not needed.
- Keep config schema authoritative in `finclaw/config/schema.py`.
- Remember that config is stored on disk in camelCase but used in Python as snake_case via `config/loader.py`.

### Functions And Classes

- Add docstrings on modules, public classes, and non-obvious public methods.
- Keep docstrings concise and practical.
- Prefer early returns over deeply nested conditionals.
- When behavior branches by domain, route through the owning router or manager instead of growing one large function.

### Comments

- Add comments only when the code's intent is not obvious from names and structure.
- Good comment targets in this repo: security constraints, protocol behavior, runtime/workspace distinctions, and provider-specific quirks.
- Do not add narration comments for straightforward assignments or control flow.

## Async And Concurrency

- Keep async boundaries explicit. Use `async def` only where IO or async coordination is actually involved.
- Do not block the event loop with avoidable synchronous network or filesystem work inside long-running async paths.
- Use `asyncio.create_task()` only for independently managed background work.
- When stopping services, clean up tasks, sockets, and connections in the same owner class that created them.

## Logging, Errors, And Operator Output

- Use `loguru.logger` for runtime/service logging in Python modules.
- Use `console.print()` in CLI command flows where output is meant for the human operator.
- Avoid raw `print()` in Python except where the file already clearly behaves like a low-level bootstrap script.
- Log enough context to debug failures, but do not dump secrets, tokens, or private keys.
- Fail loudly on invalid configuration and fail closed on security-sensitive defaults.
- Prefer actionable error messages over generic exceptions.

## Architecture-Specific Guidance

### CLI

- Keep user-facing command behavior in `finclaw/cli/commands.py`.
- New commands should follow existing Typer patterns, help text style, and console output conventions.

### Agent Loop And Tools

- Register new tools in `AgentLoop._register_default_tools()`.
- Keep tool implementations narrow and composable.
- Do not bury routing rules inside unrelated tools when a router already owns that decision.

### Financial Features

- Put decision logic in `finclaw/agent/financial/`.
- Put concrete data access or execution logic in `finclaw/agent/financial_tools/`.
- If a feature needs persistence, use the existing profile, history, cache, or memory layers instead of inventing a new ad hoc file.

### Channels

- Keep platform-specific behavior inside the relevant adapter in `finclaw/channels/`.
- Shared policy decisions belong in shared channel infrastructure, not duplicated in every adapter.
- Default to secure configuration and explicit allowlists unless the task requires broader access.

### Runtime Prompt Bootstrap

- Repository docs are not automatically part of the runtime prompt.
- Changes to root `AGENTS.md` or `CODEBASE.md` help contributors and coding agents.
- Changes to runtime `AGENTS.md`, `SOUL.md`, `USER.md`, or `TOOLS.md` must go through workspace template generation and context loading logic.

## TypeScript Bridge Style

- Match the bridge's strict TypeScript configuration.
- Prefer explicit interfaces and narrow unions for message payloads.
- Avoid `any` unless a boundary truly cannot be typed and the reason is local and obvious.
- Keep Node/WebSocket lifecycle management explicit: setup, auth, message handling, cleanup.
- Use `console.log`, `console.warn`, and `console.error` in the bridge consistently with current files.

## Security And State

- Treat config, session files, message history, auth directories, tokens, cookies, and wallet keys as sensitive.
- Do not log secrets.
- Prefer fail-closed defaults for access control, bridge exposure, and external connections.
- Keep persistence paths centralized through helper/config functions rather than hardcoding duplicate path logic.

## Documentation Style

- Keep README content user-facing and product-oriented.
- Keep `AGENTS.md`, `CODEBASE.md`, and this file dense, operational, and optimized for fast repository orientation.
- When adding a new agent-facing doc, link it from `README.md` and `AGENTS.md` if it should be part of the standard reading path.

## Change Discipline

- Do not reformat unrelated code.
- Do not rename symbols, files, or config keys without a concrete reason.
- Do not add new dependencies when the standard library or existing dependency set already solves the problem adequately.
- Prefer extending existing managers, routers, and schemas over parallel one-off implementations.

## Validation Expectations

Choose validation that matches the surface you changed:

- Python: `ruff check finclaw`
- CLI/setup paths: `python -m finclaw --version`, `finclaw status`, or a focused command smoke test
- Bridge: `npm run build` inside `bridge/`
- Docs: verify links, file names, and that repo docs are not confused with runtime workspace bootstrap files

## Avoid These Patterns

- Generic helper layers that hide the real owner of behavior.
- Silent exception swallowing without logging.
- New state files when an existing memory, history, cache, config, or session surface already fits.
- Raw provider-, channel-, or tool-specific branching copied into multiple modules.
- Documentation that mixes repo contributor guidance with runtime prompt instructions.