# TTFL Lab Impact
#
# Entry point
import re

from src.games import Games
from src.teams import Teams
from src.players import Players
from src.impact import Impact
from datetime import date
import sys
import getopt


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


def ttlf_lab_impact_start(day=None, season=None, season_type=None, force_refresh=False):
    if not day:
        day = date.today().strftime("%m/%d/%Y")
    if not season:
        season = "2022-23"
    if not season_type:
        season_type = 'RegularSeason'

    teams = Teams()
    players = Players()
    games = Games(season)
    impact = Impact()

    # 1. Refresh databases
    refresh_databases(season, games, teams, players, force_refresh=force_refresh)

    # 2. Fetch day games
    today_games_df = games.list_daily_games(day, force_refresh=force_refresh)
    if len(today_games_df.index) == 0:
        print('No game for this date: ' + day)
        sys.exit()

    today_team_ids = today_games_df['TEAM_HOME_ID'].tolist() + today_games_df['TEAM_AWAY_ID'].tolist()
    today_players_df = players.fetch_player_by_teams(today_team_ids, force_refresh=force_refresh)
    today_player_ids = today_players_df['PERSON_ID'].to_list()
    today_player_box_scores = games.get_box_scores_for_players(today_player_ids, day, season_type)

    # 3. Compute prediction
    impact.compute_impact(day, season, today_games_df, today_players_df, today_player_box_scores)


def print_help():
    print('app.py -d <day_to_generate> -f <force_refresh> -s <season> -t <season_type>')
    print('\t<day_to_generate> mm/dd/yyyy (default: today)')
    print('\t<force_refresh> True or False (default: False)')
    print('\t<season> yyyy-yy (default: 2022-23)')
    print('\t<season_type> RegularSeason, PlayOff (default: RegularSeason)')


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hd:f:s:t:",
                                   ["help", "day=", "force-refresh=", "season=", "season-type="])
    except getopt.GetoptError:
        print_help()
        sys.exit(2)

    arg_force_refresh = False
    arg_day = None
    arg_season = None
    arg_season_type = None

    for opt, arg in opts:
        if opt in ("-d", "--day"):
            arg_day = arg
        elif opt in ("-f", "--force-refresh"):
            arg_force_refresh = bool(arg)
        elif opt in ("-s", "--season"):
            arg_season = arg
        elif opt in ("-t", "--season-type"):
            arg_season_type = arg
        else:
            print_help()
            sys.exit()

    ttlf_lab_impact_start(day=arg_day, force_refresh=arg_force_refresh)
