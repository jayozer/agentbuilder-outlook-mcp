# Repository Guidelines

## Project Structure & Module Organization
- `mcp_outlook/` hosts runtime code: `auth.py` manages Graph tokens, `config.py` loads environment variables, and `email.py` enforces payload validation.
- `server.py` exposes the FastMCP tool declared in `fastmcp.json`; treat it as the entrypoint for agents.
- `tests/` mirrors package modules with `pytest` suites; regenerate `build/` and `mcp_outlook.egg-info/` only when packaging a release.

## Build, Test, and Development Commands
- `uv pip install .[dev]` installs runtime dependencies plus `pytest`.
- `fastmcp run server.py` starts the stdio MCP server for interactive testing.
- `pytest` (e.g., `pytest -k send_mail`) executes the suite; add `-vv` when chasing failures.
- Run the dry-run snippet in `README.md` to preview `send_outlook_mail_impl` payloads without sending mail.

## Coding Style & Naming Conventions
- Target Python 3.10+, four-space indentation, and double-quoted strings to stay consistent.
- Use type hints and `pydantic` models for new inputs; prefer raising `GraphAuthError`/`ConfigurationError` for domain failures.
- Keep functions and variables `snake_case`, classes `PascalCase`, and log through module-level loggers.
- Reserve comments for intent or edge cases; keep docstrings brief but descriptive when behavior is non-obvious.

## Testing Guidelines
- Place new tests in `tests/` with filenames `test_<module>.py` and functions beginning with `test_`.
- Mock Microsoft Graph with `httpx.MockTransport` or fixtures; cover delegated-token and client-credential flows plus validation errors.
- Assert on both success payloads and failure messages, and seed `os.environ` via fixtures when configuration matters.

## Commit & Pull Request Guidelines
- The scaffold ships without VCS history; follow Conventional Commits (`feat:`, `fix:`, `docs:`) with imperative summaries under 72 characters.
- Note configuration changes (env vars, FastMCP metadata) in the commit body and reference related issues in PR descriptions.
- PRs should list test evidence (`pytest`, dry-run preview) and attach payload snippets or logs when changing Graph interactions.

## Security & Configuration Tips
- Keep secrets out of version control; rely on `.env` loaded through `mcp_outlook.config`.
- Validate new logic with `dry_run=True` before sending live email and scope credentials to `Mail.Send`.
- Avoid logging raw tokens or addresses; scrub values before raising log levels in production.
