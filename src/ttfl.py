# TTFL Lab Impact
#
# TTFL
#
# TTLF Impact Entry Points


from src.games import Games
from src.impact import Impact
from src.injuries import Injuries
from src.players import Players
from src.teams import Teams
from datetime import date
from datetime import datetime
import sys


def ttlf_lab_impact_start(day=None, season=None, season_type=None, force_refresh=False):
    if not day:
        day = date.today().strftime("%m/%d/%Y")
    if not season:
        season = "2023-24"
    if not season_type:
        season_type = 'RegularSeason'

    teams = Teams()
    players = Players()
    games = Games(season)
    impact = Impact()

    # 1. Refresh databases
    if force_refresh:
        refresh_databases(season, games, teams, players, force_refresh=force_refresh)

    # 2. Fetch day games
    today_games_df = games.list_daily_games(day, force_refresh=force_refresh)
    if len(today_games_df.index) == 0:
        print('No game for this date: ' + day)
        sys.exit()

    today_team_ids = today_games_df['TEAM_HOME_ID'].tolist() + today_games_df['TEAM_AWAY_ID'].tolist()
    today_players_df = players.fetch_player_by_teams(today_team_ids, force_refresh=force_refresh)
    today_player_ids = today_players_df['PERSON_ID'].to_list()
    today_box_scores = games.get_box_scores_for_players(today_player_ids, day, season_type)

    # 3. Fetch Injury Report
    injuries = Injuries()
    injury_report = injuries.load_injury_report()

    # 3. Compute prediction
    impact_table = impact.compute_impact(day, season, today_games_df, today_players_df, today_box_scores, injury_report)
    date_object = datetime.strptime(day, "%m/%d/%Y")
    metadata = impact.get_impact_metadata(date_object, today_games_df)
    filename = impact.save_impact(day, impact_table, metadata)

    print("Successfully wrote impact on: ", filename)

    return filename


def refresh_databases(season, games, teams, players, force_refresh=False):
    # Fetch all box scores
    print("Fetching season " + season + " games...")
    [all_box_scores_df, box_score_succeed] = games.fetch_season_box_scores(season, force_refresh=force_refresh)

    # Fetch all teams
    print("Fetching teams...")
    team_id_list = all_box_scores_df['TEAM_ID'].unique().tolist()
    [all_team_info_df, team_succeed] = teams.fetch_all_team_info(team_id_list)

    # Fetch all players
    print("Fetching players...")
    player_id_list = all_box_scores_df['PLAYER_ID'].unique().tolist()
    [all_player_info_df, player_succeed] = players.fetch_all_player_info(player_id_list)

    # Display at the end to show results
    if box_score_succeed:
        print("Fetching season " + season + " box scores success.")
    else:
        print("Fetching season " + season + " box scores done with errors.")
    if team_succeed:
        print("Fetching teams success.")
    else:
        print("Fetching teams done with errors.")
    if player_succeed:
        print("Fetching players success.")
    else:
        print("Fetching players done with errors.")

    if box_score_succeed and team_succeed and player_succeed:
        print("Ending without error.")
    else:
        print("Ending with errors.")
