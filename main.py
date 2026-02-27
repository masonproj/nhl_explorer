import logging
import time

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(title="NHL Explorer")
templates = Jinja2Templates(directory="templates")

NHL_API = "https://api-web.nhle.com/v1"
_cache: dict = {}

TEAMS = {
    "ANA": "Anaheim Ducks",
    "BOS": "Boston Bruins",
    "BUF": "Buffalo Sabres",
    "CGY": "Calgary Flames",
    "CAR": "Carolina Hurricanes",
    "CHI": "Chicago Blackhawks",
    "COL": "Colorado Avalanche",
    "CBJ": "Columbus Blue Jackets",
    "DAL": "Dallas Stars",
    "DET": "Detroit Red Wings",
    "EDM": "Edmonton Oilers",
    "FLA": "Florida Panthers",
    "LAK": "Los Angeles Kings",
    "MIN": "Minnesota Wild",
    "MTL": "Montreal Canadiens",
    "NSH": "Nashville Predators",
    "NJD": "New Jersey Devils",
    "NYI": "New York Islanders",
    "NYR": "New York Rangers",
    "OTT": "Ottawa Senators",
    "PHI": "Philadelphia Flyers",
    "PIT": "Pittsburgh Penguins",
    "SJS": "San Jose Sharks",
    "SEA": "Seattle Kraken",
    "STL": "St. Louis Blues",
    "TBL": "Tampa Bay Lightning",
    "TOR": "Toronto Maple Leafs",
    "UTA": "Utah Hockey Club",
    "VAN": "Vancouver Canucks",
    "VGK": "Vegas Golden Knights",
    "WSH": "Washington Capitals",
    "WPG": "Winnipeg Jets",
}

STAT_CATEGORIES = {
    "points": "Points",
    "goals": "Goals",
    "assists": "Assists",
    "plusMinus": "Plus/Minus",
    "ppGoals": "Power Play Goals",
    "gameWinningGoals": "Game Winning Goals",
    "shots": "Shots",
}

VALID_CONFERENCES = {"All", "Eastern", "Western"}
VALID_LIMITS = {10, 20, 30, 50}


async def fetch(url: str, ttl: int = 300) -> dict:
    now = time.time()
    if url in _cache and now - _cache[url]["ts"] < ttl:
        return _cache[url]["data"]
    async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
        r = await client.get(url)
        r.raise_for_status()
        data = r.json()
    _cache[url] = {"data": data, "ts": now}
    return data


def _api_error(e: Exception) -> str:
    if isinstance(e, httpx.TimeoutException):
        logger.warning("NHL API request timed out")
        return "The request timed out. Please try again."
    if isinstance(e, httpx.HTTPStatusError):
        logger.error("NHL API returned HTTP %s", e.response.status_code)
        return f"NHL API error ({e.response.status_code}). Try again later."
    if isinstance(e, httpx.RequestError):
        logger.error("Network error contacting NHL API: %s", e)
        return "A network error occurred."
    logger.exception("Unexpected error in NHL API call")
    return "An unexpected error occurred."


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/scores", response_class=HTMLResponse)
async def scores(request: Request):
    error = None
    games: list = []
    date = ""
    try:
        data = await fetch(f"{NHL_API}/schedule/now", ttl=60)
        week = data.get("gameWeek", [])
        if week:
            games = week[0].get("games", [])
            date = week[0].get("date", "")
    except Exception as e:
        error = _api_error(e)
    return templates.TemplateResponse(
        "partials/scores.html",
        {"request": request, "games": games, "date": date, "error": error},
    )


@app.get("/standings", response_class=HTMLResponse)
async def standings(request: Request, conference: str = "All"):
    if conference not in VALID_CONFERENCES:
        conference = "All"
    error = None
    rows: list = []
    try:
        data = await fetch(f"{NHL_API}/standings/now")
        rows = data.get("standings", [])
        if conference != "All":
            rows = [t for t in rows if t.get("conferenceName") == conference]
        rows.sort(key=lambda t: (t.get("points", 0), t.get("wins", 0)), reverse=True)
    except Exception as e:
        error = _api_error(e)
    return templates.TemplateResponse(
        "partials/standings.html",
        {"request": request, "standings": rows, "conference": conference, "error": error},
    )


@app.get("/leaders", response_class=HTMLResponse)
async def leaders(request: Request, category: str = "points", limit: int = 20):
    if category not in STAT_CATEGORIES:
        category = "points"
    if limit not in VALID_LIMITS:
        limit = 20
    error = None
    players: list = []
    try:
        data = await fetch(
            f"{NHL_API}/skater-stats-leaders/current?categories={category}&limit={limit}"
        )
        players = data.get(category, [])
    except Exception as e:
        error = _api_error(e)
    return templates.TemplateResponse(
        "partials/leaders.html",
        {
            "request": request,
            "players": players,
            "category": category,
            "limit": limit,
            "error": error,
            "categories": STAT_CATEGORIES,
        },
    )


@app.get("/roster", response_class=HTMLResponse)
async def roster(request: Request, team: str = "BOS"):
    if team not in TEAMS:
        team = "BOS"
    error = None
    forwards: list = []
    defensemen: list = []
    goalies: list = []
    try:
        data = await fetch(f"{NHL_API}/roster/{team}/current")
        forwards = data.get("forwards", [])
        defensemen = data.get("defensemen", [])
        goalies = data.get("goalies", [])
    except Exception as e:
        error = _api_error(e)
    return templates.TemplateResponse(
        "partials/roster.html",
        {
            "request": request,
            "forwards": forwards,
            "defensemen": defensemen,
            "goalies": goalies,
            "team": team,
            "teams": TEAMS,
            "error": error,
        },
    )
