# NHL Explorer

FastAPI + HTMX app that displays live NHL scores, standings, stat leaders, and team rosters
using the public NHL API (https://api-web.nhle.com/v1).

## Dev Commands

| Task | Command |
|---|---|
| Run dev server | `uvicorn main:app --reload` |
| Run tests | `pytest tests/ -v` |
| Install deps | `pip install -r requirements.txt` |
| Install test deps | `pip install -r requirements-dev.txt` |

## Architecture

- `main.py` — all routes, in-memory TTL cache, input validation, error handling
- `templates/index.html` — shell page (loads HTMX + Tailwind; all content swapped via HTMX)
- `templates/partials/` — one HTML fragment per tab: scores, standings, leaders, roster
- `tests/test_main.py` — 15 async tests using httpx ASGITransport; all NHL API calls mocked

## Key Patterns

**Input validation** — every query param is checked against an allowlist before use.
Invalid values fall back silently to the parameter default. Allowlists live in `main.py`:
- `TEAMS` keys → `team`
- `STAT_CATEGORIES` keys → `category`
- `VALID_CONFERENCES` → `conference`
- `VALID_LIMITS` → `limit`

**Error handling** — always use the `_api_error(e)` helper in `except` clauses.
It classifies `httpx` exceptions, logs them at the right level, and returns a
user-facing string. Never use `str(e)` or a bare `except` directly.

**Testing** — mock `main.fetch` via `unittest.mock.AsyncMock`. Never make real
HTTP calls in tests.

**Caching** — use `await fetch(url, ttl=N)` in routes; do not call `httpx` directly.

## Constraints

- Do not add dependencies without pinning them in `requirements.txt`
- Partial templates must be self-contained HTML fragments (no `<html>`/`<body>` wrapper)
- Keep all route logic in `main.py` — no separate routers needed at this scale
