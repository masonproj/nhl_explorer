import streamlit as st
import requests
import pandas as pd

NHL_API = "https://api-web.nhle.com/v1"

st.set_page_config(page_title="NHL Explorer", layout="wide")
st.title("NHL Explorer")


@st.cache_data(ttl=300)
def get_standings():
    r = requests.get(f"{NHL_API}/standings/now")
    r.raise_for_status()
    return r.json().get("standings", [])


@st.cache_data(ttl=60)
def get_schedule_today():
    r = requests.get(f"{NHL_API}/schedule/now")
    r.raise_for_status()
    data = r.json()
    game_weeks = data.get("gameWeek", [])
    if not game_weeks:
        return []
    return game_weeks[0].get("games", [])


@st.cache_data(ttl=300)
def get_skater_leaders(category="points", limit=20):
    r = requests.get(f"{NHL_API}/skater-stats-leaders/current?categories={category}&limit={limit}")
    r.raise_for_status()
    return r.json()


@st.cache_data(ttl=300)
def get_team_roster(team_abbrev):
    r = requests.get(f"{NHL_API}/roster/{team_abbrev}/current")
    r.raise_for_status()
    return r.json()


@st.cache_data(ttl=300)
def get_player(player_id):
    r = requests.get(f"{NHL_API}/player/{player_id}/landing")
    r.raise_for_status()
    return r.json()


TEAMS = {
    "ANA": "Anaheim Ducks", "ARI": "Arizona Coyotes", "BOS": "Boston Bruins",
    "BUF": "Buffalo Sabres", "CGY": "Calgary Flames", "CAR": "Carolina Hurricanes",
    "CHI": "Chicago Blackhawks", "COL": "Colorado Avalanche", "CBJ": "Columbus Blue Jackets",
    "DAL": "Dallas Stars", "DET": "Detroit Red Wings", "EDM": "Edmonton Oilers",
    "FLA": "Florida Panthers", "LAK": "Los Angeles Kings", "MIN": "Minnesota Wild",
    "MTL": "Montreal Canadiens", "NSH": "Nashville Predators", "NJD": "New Jersey Devils",
    "NYI": "New York Islanders", "NYR": "New York Rangers", "OTT": "Ottawa Senators",
    "PHI": "Philadelphia Flyers", "PIT": "Pittsburgh Penguins", "SJS": "San Jose Sharks",
    "SEA": "Seattle Kraken", "STL": "St. Louis Blues", "TBL": "Tampa Bay Lightning",
    "TOR": "Toronto Maple Leafs", "UTA": "Utah Hockey Club", "VAN": "Vancouver Canucks",
    "VGK": "Vegas Golden Knights", "WSH": "Washington Capitals", "WPG": "Winnipeg Jets",
}

tab_standings, tab_scores, tab_leaders, tab_teams = st.tabs(
    ["Standings", "Today's Games", "Stat Leaders", "Team Roster"]
)

# ── STANDINGS ────────────────────────────────────────────────────────────────
with tab_standings:
    st.header("Current Standings")
    conference_filter = st.selectbox(
        "Conference", ["All", "Eastern", "Western"], key="conf"
    )
    try:
        standings = get_standings()
        rows = []
        for team in standings:
            conf = team.get("conferenceName", "")
            if conference_filter != "All" and conf != conference_filter:
                continue
            rows.append({
                "Team": team.get("teamName", {}).get("default", ""),
                "Conference": conf,
                "Division": team.get("divisionName", ""),
                "GP": team.get("gamesPlayed", 0),
                "W": team.get("wins", 0),
                "L": team.get("losses", 0),
                "OTL": team.get("otLosses", 0),
                "Pts": team.get("points", 0),
                "GF": team.get("goalFor", 0),
                "GA": team.get("goalAgainst", 0),
                "Pct": f"{team.get('pointPctg', 0):.3f}",
            })
        if rows:
            df = pd.DataFrame(rows).sort_values("Pts", ascending=False).reset_index(drop=True)
            df.index += 1
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No standings data available.")
    except Exception as e:
        st.error(f"Failed to load standings: {e}")

# ── TODAY'S GAMES ────────────────────────────────────────────────────────────
with tab_scores:
    st.header("Today's Games")
    if st.button("Refresh", key="refresh_scores"):
        get_schedule_today.clear()
    try:
        games = get_schedule_today()
        if not games:
            st.info("No games scheduled today.")
        for game in games:
            away = game.get("awayTeam", {})
            home = game.get("homeTeam", {})
            state = game.get("gameState", "")
            away_name = away.get("placeName", {}).get("default", away.get("abbrev", ""))
            home_name = home.get("placeName", {}).get("default", home.get("abbrev", ""))
            away_score = away.get("score", "-")
            home_score = home.get("score", "-")

            with st.container(border=True):
                c1, c2, c3 = st.columns([2, 1, 2])
                with c1:
                    st.markdown(f"### {away_name}")
                    st.markdown(f"**{away.get('abbrev', '')}**")
                with c2:
                    if state in ("LIVE", "CRIT"):
                        period = game.get("period", "")
                        time_rem = game.get("clock", {}).get("timeRemaining", "")
                        st.markdown(f"## {away_score} – {home_score}")
                        st.markdown(f"*P{period} {time_rem}*")
                    elif state == "FINAL":
                        st.markdown(f"## {away_score} – {home_score}")
                        st.markdown("*Final*")
                    else:
                        start = game.get("startTimeUTC", "TBD")
                        st.markdown("### vs")
                        st.caption(start[:16].replace("T", " ") + " UTC")
                with c3:
                    st.markdown(f"### {home_name}")
                    st.markdown(f"**{home.get('abbrev', '')}**")
    except Exception as e:
        st.error(f"Failed to load today's games: {e}")

# ── STAT LEADERS ─────────────────────────────────────────────────────────────
with tab_leaders:
    st.header("Skater Stat Leaders")
    stat_options = {
        "Points": "points",
        "Goals": "goals",
        "Assists": "assists",
        "Plus/Minus": "plusMinus",
        "Power Play Goals": "ppGoals",
        "Game Winning Goals": "gameWinningGoals",
    }
    selected_stat_label = st.selectbox("Stat Category", list(stat_options.keys()), key="stat_cat")
    selected_stat = stat_options[selected_stat_label]
    limit = st.slider("Top N players", 5, 50, 20, key="stat_limit")

    try:
        leaders_data = get_skater_leaders(selected_stat, limit)
        category_data = leaders_data.get(selected_stat, [])
        if category_data:
            rows = []
            for player in category_data:
                rows.append({
                    "Player": f"{player.get('firstName', {}).get('default', '')} {player.get('lastName', {}).get('default', '')}",
                    "Team": player.get("teamAbbrev", ""),
                    "Position": player.get("position", ""),
                    selected_stat_label: player.get("value", 0),
                })
            df = pd.DataFrame(rows)
            df.index += 1
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No leader data available.")
    except Exception as e:
        st.error(f"Failed to load stat leaders: {e}")

# ── TEAM ROSTER ──────────────────────────────────────────────────────────────
with tab_teams:
    st.header("Team Roster")
    team_abbrev = st.selectbox(
        "Select Team",
        options=list(TEAMS.keys()),
        format_func=lambda k: f"{k} – {TEAMS[k]}",
        key="team_select",
    )

    try:
        roster = get_team_roster(team_abbrev)
        for group_key, group_label in [("forwards", "Forwards"), ("defensemen", "Defensemen"), ("goalies", "Goalies")]:
            players = roster.get(group_key, [])
            if not players:
                continue
            st.subheader(group_label)
            rows = []
            for p in players:
                rows.append({
                    "#": p.get("sweaterNumber", ""),
                    "Name": f"{p.get('firstName', {}).get('default', '')} {p.get('lastName', {}).get('default', '')}",
                    "Position": p.get("positionCode", ""),
                    "Shoots/Catches": p.get("shootsCatches", ""),
                    "Height": p.get("heightInInches", ""),
                    "Weight (lbs)": p.get("weightInPounds", ""),
                    "Born": p.get("birthDate", ""),
                    "Birthplace": p.get("birthCity", {}).get("default", ""),
                })
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

        if st.checkbox("Show full player details", key="player_detail_toggle"):
            all_players = roster.get("forwards", []) + roster.get("defensemen", []) + roster.get("goalies", [])
            names = {
                f"{p.get('firstName', {}).get('default', '')} {p.get('lastName', {}).get('default', '')}": p.get("id")
                for p in all_players
            }
            chosen_name = st.selectbox("Pick a player", list(names.keys()), key="chosen_player")
            player_id = names[chosen_name]
            try:
                player_info = get_player(player_id)
                col1, col2 = st.columns(2)
                with col1:
                    headshot = player_info.get("headshot", "")
                    if headshot:
                        st.image(headshot, width=180)
                with col2:
                    st.markdown(f"**{chosen_name}**")
                    st.write(f"Position: {player_info.get('position', '')}")
                    st.write(f"Jersey #: {player_info.get('sweaterNumber', '')}")
                    st.write(f"Born: {player_info.get('birthDate', '')} in {player_info.get('birthCity', {}).get('default', '')}")
                    st.write(f"Nationality: {player_info.get('birthCountry', '')}")

                season_stats = player_info.get("featuredStats", {}).get("regularSeason", {}).get("subSeason", {})
                if season_stats:
                    st.subheader("Current Season Stats")
                    stat_items = {k: v for k, v in season_stats.items() if isinstance(v, (int, float))}
                    st.dataframe(
                        pd.DataFrame([stat_items]).T.rename(columns={0: "Value"}),
                        use_container_width=True,
                    )
            except Exception as e:
                st.error(f"Could not load player details: {e}")
    except Exception as e:
        st.error(f"Failed to load roster: {e}")
