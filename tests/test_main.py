"""Tests for NHL Explorer endpoints."""
from unittest.mock import AsyncMock, patch

import httpx
import pytest

from main import app

pytestmark = pytest.mark.asyncio


async def _get(path: str) -> httpx.Response:
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        return await client.get(path)


# ---------------------------------------------------------------------------
# Index
# ---------------------------------------------------------------------------

async def test_index_returns_200():
    r = await _get("/")
    assert r.status_code == 200
    assert "NHL Explorer" in r.text


# ---------------------------------------------------------------------------
# /scores
# ---------------------------------------------------------------------------

SCORES_DATA = {
    "gameWeek": [
        {
            "date": "2026-02-27",
            "games": [
                {
                    "gameState": "FINAL",
                    "awayTeam": {
                        "abbrev": "TOR",
                        "score": 3,
                        "logo": "",
                        "placeName": {"default": "Toronto"},
                    },
                    "homeTeam": {
                        "abbrev": "BOS",
                        "score": 2,
                        "logo": "",
                        "placeName": {"default": "Boston"},
                    },
                }
            ],
        }
    ]
}


async def test_scores_happy_path():
    with patch("main.fetch", new_callable=AsyncMock, return_value=SCORES_DATA):
        r = await _get("/scores")
    assert r.status_code == 200
    assert "TOR" in r.text
    assert "BOS" in r.text
    assert "2026-02-27" in r.text


async def test_scores_no_games():
    with patch("main.fetch", new_callable=AsyncMock, return_value={"gameWeek": []}):
        r = await _get("/scores")
    assert r.status_code == 200
    assert "No games scheduled" in r.text


async def test_scores_timeout_shows_error():
    with patch("main.fetch", new_callable=AsyncMock, side_effect=httpx.TimeoutException("t/o")):
        r = await _get("/scores")
    assert r.status_code == 200
    assert "timed out" in r.text.lower()


# ---------------------------------------------------------------------------
# /standings
# ---------------------------------------------------------------------------

STANDINGS_DATA = {
    "standings": [
        {
            "conferenceName": "Eastern",
            "divisionName": "Atlantic",
            "teamName": {"default": "Boston Bruins"},
            "teamLogo": "",
            "points": 80,
            "wins": 38,
            "losses": 20,
            "otLosses": 4,
            "gamesPlayed": 62,
            "goalFor": 200,
            "goalAgainst": 170,
            "pointPctg": 0.645,
        },
        {
            "conferenceName": "Western",
            "divisionName": "Central",
            "teamName": {"default": "Colorado Avalanche"},
            "teamLogo": "",
            "points": 75,
            "wins": 35,
            "losses": 22,
            "otLosses": 5,
            "gamesPlayed": 62,
            "goalFor": 195,
            "goalAgainst": 180,
            "pointPctg": 0.605,
        },
    ]
}


async def test_standings_all_conferences():
    with patch("main.fetch", new_callable=AsyncMock, return_value=STANDINGS_DATA):
        r = await _get("/standings")
    assert r.status_code == 200
    assert "Boston Bruins" in r.text
    assert "Colorado Avalanche" in r.text


async def test_standings_eastern_filter():
    with patch("main.fetch", new_callable=AsyncMock, return_value=STANDINGS_DATA):
        r = await _get("/standings?conference=Eastern")
    assert r.status_code == 200
    assert "Boston Bruins" in r.text
    assert "Colorado Avalanche" not in r.text


async def test_standings_invalid_conference_falls_back_to_all():
    with patch("main.fetch", new_callable=AsyncMock, return_value=STANDINGS_DATA):
        r = await _get("/standings?conference=INVALID")
    assert r.status_code == 200
    # Both teams present since invalid conference → All
    assert "Boston Bruins" in r.text
    assert "Colorado Avalanche" in r.text


async def test_standings_http_error_shows_error():
    mock_response = httpx.Response(503)
    exc = httpx.HTTPStatusError("bad", request=httpx.Request("GET", "http://x"), response=mock_response)
    with patch("main.fetch", new_callable=AsyncMock, side_effect=exc):
        r = await _get("/standings")
    assert r.status_code == 200
    assert "503" in r.text


# ---------------------------------------------------------------------------
# /leaders
# ---------------------------------------------------------------------------

LEADERS_DATA = {
    "goals": [
        {
            "firstName": {"default": "Auston"},
            "lastName": {"default": "Matthews"},
            "teamAbbrev": "TOR",
            "position": "C",
            "headshot": "",
            "value": 42,
        }
    ]
}


async def test_leaders_happy_path():
    with patch("main.fetch", new_callable=AsyncMock, return_value=LEADERS_DATA):
        r = await _get("/leaders?category=goals")
    assert r.status_code == 200
    assert "Matthews" in r.text


async def test_leaders_invalid_category_falls_back_to_points():
    # When category=INVALID fetch will be called with category="points"
    points_data = {
        "points": [
            {
                "firstName": {"default": "Connor"},
                "lastName": {"default": "McDavid"},
                "teamAbbrev": "EDM",
                "position": "C",
                "headshot": "",
                "value": 100,
            }
        ]
    }
    with patch("main.fetch", new_callable=AsyncMock, return_value=points_data):
        r = await _get("/leaders?category=INVALID")
    assert r.status_code == 200
    assert "McDavid" in r.text


async def test_leaders_invalid_limit_falls_back_to_20():
    points_data = {"points": []}
    with patch("main.fetch", new_callable=AsyncMock, return_value=points_data) as mock_fetch:
        r = await _get("/leaders?limit=999")
    assert r.status_code == 200
    # Verify the URL used limit=20
    called_url = mock_fetch.call_args[0][0]
    assert "limit=20" in called_url


async def test_leaders_timeout_shows_error():
    with patch("main.fetch", new_callable=AsyncMock, side_effect=httpx.TimeoutException("t/o")):
        r = await _get("/leaders")
    assert r.status_code == 200
    assert "timed out" in r.text.lower()


# ---------------------------------------------------------------------------
# /roster
# ---------------------------------------------------------------------------

ROSTER_DATA = {
    "forwards": [
        {
            "sweaterNumber": 34,
            "firstName": {"default": "Auston"},
            "lastName": {"default": "Matthews"},
            "positionCode": "C",
            "shootsCatches": "L",
            "heightInInches": 75,
            "weightInPounds": 208,
            "birthDate": "1997-09-17",
            "birthCity": {"default": "San Ramon"},
            "birthStateProvince": {"default": "CA"},
            "headshot": "",
        }
    ],
    "defensemen": [],
    "goalies": [],
}


async def test_roster_happy_path():
    with patch("main.fetch", new_callable=AsyncMock, return_value=ROSTER_DATA):
        r = await _get("/roster?team=TOR")
    assert r.status_code == 200
    assert "Matthews" in r.text


async def test_roster_invalid_team_falls_back_to_bos():
    bos_data = {"forwards": [], "defensemen": [], "goalies": []}
    with patch("main.fetch", new_callable=AsyncMock, return_value=bos_data) as mock_fetch:
        r = await _get("/roster?team=XXX")
    assert r.status_code == 200
    called_url = mock_fetch.call_args[0][0]
    assert "/roster/BOS/" in called_url


async def test_roster_network_error_shows_error():
    with patch(
        "main.fetch",
        new_callable=AsyncMock,
        side_effect=httpx.ConnectError("refused"),
    ):
        r = await _get("/roster")
    assert r.status_code == 200
    assert "error" in r.text.lower()
