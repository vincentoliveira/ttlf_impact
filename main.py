# TTFL Lab Impact
#
# Entry point
import re

from src.games import Games
from src.teams import Teams
from src.players import Players
from src.impact import Impact


def refresh_databases(season, games, teams, players):
    # Fetch all box scores
    print("Fetching season " + season + " games...")
    [all_box_scores_df, box_score_succeed] = games.fetch_season_box_scores(season)

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
    if team_succeed:
        print("Fetching players success.")
    else:
        print("Fetching players done with errors.")

    if box_score_succeed and team_succeed and player_succeed:
        print("Ending without error.")
    else:
        print("Ending with errors.")

def ttlf_lab_impact_start():
    season = "2022-23"
    season_type = 'SR'
    day = "03/02/2023"
    games = Games(buffer_size=16)
    teams = Teams()
    players = Players()
    predictions = Impact()

    # 1. Refresh databases
    refresh_databases(season, games, teams, players)

    # 2. Fetch day games
    today_games_df = games.list_daily_games(day)
    today_team_ids = today_games_df['TEAM_ID'].tolist()
    today_players_df = players.fetch_player_by_teams(today_team_ids)
    today_player_ids = today_players_df['PERSON_ID'].to_list()
    today_player_box_scores = games.get_box_scores_for_players(today_player_ids, day, season_type)

    # 3. Compute prediction
    predictions.compute_impact(day, today_games_df, today_players_df, today_player_box_scores)

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    ttlf_lab_impact_start()
