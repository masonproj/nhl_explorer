# NHL Explorer

A lightweight web app for browsing live NHL scores, standings, stat leaders, and team rosters — built with **FastAPI**, **HTMX**, and **Tailwind CSS**.

## Tech Stack

- [FastAPI](https://fastapi.tiangolo.com/) — async Python web framework
- [HTMX](https://htmx.org/) — dynamic page updates without a JS framework
- [Tailwind CSS](https://tailwindcss.com/) — utility-first styling (via CDN)
- [httpx](https://www.python-httpx.org/) — async HTTP client for the NHL API
- [Jinja2](https://jinja.palletsprojects.com/) — HTML templating

Data is sourced from the public [NHL API](https://api-web.nhle.com/v1).

---

## Setup

```bash
git clone <repo-url>
cd nhl_explorer
pip install -r requirements.txt
```

## Run

```bash
uvicorn main:app --reload
```

Then open [http://localhost:8000](http://localhost:8000) in your browser.

---

## Endpoints

All endpoints return HTML fragments (intended for HTMX `hx-swap`).

| Route | Query Params | Description |
|---|---|---|
| `GET /` | — | Main shell page |
| `GET /scores` | — | Today's games and scores |
| `GET /standings` | `conference` | League standings, optionally filtered by conference |
| `GET /leaders` | `category`, `limit` | Skater stat leaders |
| `GET /roster` | `team` | Current roster for a team |

### Parameter Reference

**`/standings`**

| Param | Default | Valid Values |
|---|---|---|
| `conference` | `All` | `All`, `Eastern`, `Western` |

**`/leaders`**

| Param | Default | Valid Values |
|---|---|---|
| `category` | `points` | `points`, `goals`, `assists`, `plusMinus`, `ppGoals`, `gameWinningGoals`, `shots` |
| `limit` | `20` | `10`, `20`, `30`, `50` |

**`/roster`**

| Param | Default | Valid Values |
|---|---|---|
| `team` | `BOS` | Any NHL team abbreviation (e.g. `TOR`, `EDM`, `NYR`) |

Invalid parameter values are silently replaced with their defaults.

---

## Development

Install test dependencies:

```bash
pip install -r requirements-dev.txt
```

Run the test suite:

```bash
pytest tests/ -v
```
