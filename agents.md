# Agents Guide — NHL Explorer

## Environment Setup

```bash
pip install -r requirements.txt -r requirements-dev.txt
```

## Running Tests

```bash
pytest tests/ -v
```

Expected: **15 passed**. Tests use `httpx.ASGITransport` to exercise the FastAPI app
in-process — no running server required. All NHL API calls are mocked with
`unittest.mock.AsyncMock`.

## Running the App

```bash
uvicorn main:app --reload
# Open http://localhost:8000
```

## Project Layout

```
main.py              # All routes, fetch helper, validation, error handling
requirements.txt     # Pinned runtime dependencies
requirements-dev.txt # Pinned test dependencies
pytest.ini           # asyncio_mode = auto
templates/
  index.html         # Shell page (HTMX + Tailwind)
  partials/          # HTMX response fragments (one per tab)
    scores.html
    standings.html
    leaders.html
    roster.html
tests/
  test_main.py       # Full endpoint test suite
```

## Adding a New Endpoint

1. Add a route in `main.py` returning `HTMLResponse`
2. Create a partial template in `templates/partials/`
3. Validate every query param against an allowlist constant; fall back to a safe default
4. Use `_api_error(e)` in the `except` clause
5. Write tests: happy path, invalid inputs, at least one network-error case
6. Add a nav `<button>` with the matching `hx-get` in `templates/index.html`

## Code Conventions

- **Validation**: allowlist sets/dicts, silent fallback to default
- **Errors**: `_api_error(e)` only — never `str(e)` or bare `except`
- **Logging**: module-level `logger = logging.getLogger(__name__)`
- **HTTP**: always go through `fetch(url, ttl)` — never call `httpx` directly in routes
- **Dependencies**: pin new packages in `requirements.txt` immediately
