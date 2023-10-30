# TTFL Lab Impact
#
# Games
#
# Fetch Game Information

from src.singleton_meta import SingletonMeta
from nba_api.stats.endpoints import leaguegamefinder, boxscoretraditionalv2
from nba_api.stats.library.parameters import LeagueIDNullable
from src.players import Players
from src.teams import Teams
import re
import requests
import pandas as pd
import sys
from datetime import date, datetime, timedelta

class Games(metaclass=SingletonMeta):
    def __init__(self,
                 current_season='2022-23',
                 box_score_database_filename='databases/box_scores_{season}.xlsx',
                 calendar_database_filename='databases/calendar_{season}.xlsx',
                 buffer_size=256
                 ):
        self.box_scores = {}
        self.calendar = {}
        self.current_season = current_season
        self.box_score_database_filename = box_score_database_filename
        self.calendar_database_filename = calendar_database_filename
        self.buffer_size = buffer_size

        # load initial database
        self.load_all_databases(current_season)

    def load_all_databases(self, season):
        self.load_calendar(season)
        self.load_box_scores("2022-23")
        self.load_box_scores(season)

    def load_calendar(self, season):
        calendar_filename = self.calendar_database_filename.replace('{season}', season)
        try:
            existing_season_calendar_df = pd.read_excel(calendar_filename, dtype='object')
            self.calendar[season] = existing_season_calendar_df
        except FileNotFoundError:
            print("Failed to load existing calendar database: File " + calendar_filename + " not found.", file=sys.stderr)
        except Exception as e:
            print("Failed to load calendar score database: " + str(e), file=sys.stderr)

    def load_box_scores(self, current_season):
        box_score_filename = self.box_score_database_filename.replace('{season}', current_season)
        try:
            existing_box_scores = pd.read_excel(box_score_filename, dtype='object')
            game_id_list = existing_box_scores['GAME_ID'].unique().tolist()
            for game_id in game_id_list:
                self.box_scores[game_id] = existing_box_scores[existing_box_scores['GAME_ID'] == game_id]
        except FileNotFoundError:
            print("Failed to load existing box score database: File " + box_score_filename + " not found.", file=sys.stderr)
        except Exception as e:
            print("Failed to load existing box score database: " + str(e), file=sys.stderr)

    def save_calendar(self, season):
        filename = self.calendar_database_filename.replace('{season}', season)
        print("Writing calendar database file to: " + filename)
        all_calendar_df = pd.concat(self.calendar.values())
        all_calendar_df = all_calendar_df.sort_values(['GAME_DATE'], ascending=False)
        all_calendar_df.to_excel(filename, index=False)

    def save_box_scores(self, season):
        filename = self.box_score_database_filename.replace('{season}', season)
        print("Writing box score database file to: " + filename)
        all_box_scores_df = pd.concat(self.box_scores.values())
        all_box_scores_df = all_box_scores_df[all_box_scores_df['SEASON'] == season]
        all_box_scores_df = all_box_scores_df.sort_values(['GAME_DATE'], ascending=False)
        all_box_scores_df.to_excel(filename, index=False)

        def enriched_game_list(self, season, day, game_list):
            enriched_game_list = {}

            for game in game_list:
                enriched_game_list[game['gameId']] = {
                    'GAME_ID': game['gameId'],
                    'GAME_DATE': day,
                    'SEASON_YEAR': season,
                    'MATCHUP': game['homeTeam']['teamTricode'] + ' vs. ' + game['awayTeam']['teamTricode'],
                    'TEAM_HOME_ID': game['homeTeam']['teamId'],
                    'TEAM_HOME_NAME': game['homeTeam']['teamName'],
                    'TEAM_HOME_ABBREVIATION': game['homeTeam']['teamTricode'],
                    'TEAM_AWAY_ID': game['awayTeam']['teamId'],
                    'TEAM_AWAY_NAME': game['awayTeam']['teamName'],
                    'TEAM_AWAY_ABBREVIATION': game['awayTeam']['teamTricode'],
                    'HOME_BACK_TO_BACK': False,  # need to be computed with self.back_to_back_detection()
                    'AWAY_BACK_TO_BACK': False,  # need to be computed with self.back_to_back_detection()
                }

            return enriched_game_list

    def enriched_game_list(self, season, day, game_list):
        teams = Teams()

        enriched_game_list = {}
        for game in game_list:
            home_team_id = teams.find_team_id_by_abbreviation(game['htAbbreviation'])
            away_team_id = teams.find_team_id_by_abbreviation(game['vtAbbreviation'])

            enriched_game_list[game['gameID']] = {
                'GAME_ID': game['gameID'],
                'GAME_DATE': day,
                'SEASON_YEAR': season,
                'MATCHUP': game['htAbbreviation'] + ' vs. ' + game['vtAbbreviation'],
                'TEAM_HOME_ID': home_team_id,
                'TEAM_HOME_NAME': game['htNickName'],
                'TEAM_HOME_ABBREVIATION': game['htAbbreviation'],
                'TEAM_AWAY_ID': away_team_id,
                'TEAM_AWAY_NAME': game['vtNickName'],
                'TEAM_AWAY_ABBREVIATION': game['vtAbbreviation'],
                'HOME_BACK_TO_BACK': False,  # need to be computed with self.back_to_back_detection()
                'AWAY_BACK_TO_BACK': False,  # need to be computed with self.back_to_back_detection()
            }

        return enriched_game_list

    def list_daily_games(self, day=None, league=LeagueIDNullable.nba, force_refresh=False):
        if not day:
            day = date.today().strftime("%m/%d/%Y")
            filter_day = date.today().strftime("%Y-%m-%d")
        else:
            date_object = datetime.strptime(day, "%m/%d/%Y")
            filter_day = date_object.strftime("%Y-%m-%d")

        if self.current_season in self.calendar:
            season_games_df = self.calendar[self.current_season]
            today_games_df = season_games_df[season_games_df['GAME_DATE'] == filter_day]

            if len(today_games_df.index) > 0 and not force_refresh:
                return today_games_df

        print("[Games] List game for this day: " + filter_day)
        list_games = leaguegamefinder.LeagueGameFinder(
            season_nullable=self.current_season,
            date_from_nullable=day,
            date_to_nullable=day,
            league_id_nullable=league
        )

        schedule_url = "https://stats.nba.com/stats/internationalbroadcasterschedule?LeagueID=00&Season=2023&RegionID=1&Date=%s&EST=Y" % day
        schedule_league_v2_response = requests.get(schedule_url)
        schedule_league_v2 = schedule_league_v2_response.json()
        game_list = schedule_league_v2['resultSets'][0]['NextGameList']

        #schedule_url = "https://cdn.nba.com/static/json/staticData/scheduleLeagueV2.json"
        #game_list = list(filter(lambda game_date: game_date['gameDate'].startswith(day), schedule_league_v2['leagueSchedule']['gameDates']))
        if len(game_list) == 0:
            return []

        today_games = self.enriched_game_list(self.current_season, filter_day, game_list)
        today_games_df = pd.DataFrame.from_dict(today_games.values())

        if len(today_games_df.index) > 0:
            today_games_df = today_games_df.sort_values(['GAME_DATE'], ascending=False)

        if self.current_season in self.calendar:
            calendar = self.calendar[self.current_season]
            calendar.drop(calendar[calendar['GAME_DATE'] == filter_day].index, inplace=True)
            self.calendar[self.current_season] = pd.concat([calendar, today_games_df])
            self.back_to_back_detection(self.current_season)
            self.save_calendar(self.current_season)

        return today_games_df

    def back_to_back_detection(self, season):
        calendar_df = self.calendar[season]
        for index, calendar in calendar_df.iterrows():
            game_date = calendar['GAME_DATE']
            date_yesterday = (datetime.strptime(game_date, "%Y-%m-%d") - timedelta(days=1)).strftime("%Y-%m-%d")
            home_team_id = calendar['TEAM_HOME_ID']
            away_team_id = calendar['TEAM_AWAY_ID']
            home_team_yesterday_game = calendar_df[(calendar_df['GAME_DATE'] == date_yesterday) &
                                                   ((calendar_df['TEAM_HOME_ID'] == home_team_id) |
                                                    (calendar_df['TEAM_AWAY_ID'] == home_team_id))]
            home_away_yesterday_game = calendar_df[(calendar_df['GAME_DATE'] == date_yesterday) &
                                                   ((calendar_df['TEAM_HOME_ID'] == away_team_id) |
                                                    (calendar_df['TEAM_AWAY_ID'] == away_team_id))]

            calendar_df.at[index, 'HOME_BACK_TO_BACK'] = len(home_team_yesterday_game.index) > 0
            calendar_df.at[index, 'AWAY_BACK_TO_BACK'] = len(home_away_yesterday_game.index) > 0

    def enriched_season_game_list(self, season, raw_game_list_df):
        raw_game_list_df = raw_game_list_df.drop(
            columns=['MIN', 'PTS', 'FGM', 'FGA', 'FG_PCT', 'FG3M', 'FG3A', 'FG3_PCT', 'FTM', 'FTA', 'FT_PCT', 'OREB',
                     'DREB', 'REB', 'AST', 'STL', 'BLK', 'TOV', 'PF', 'PLUS_MINUS'])

        enriched_game_list = {}
        for i, game in raw_game_list_df.iterrows():
            if game['GAME_ID'] in enriched_game_list:
                if enriched_game_list[game['GAME_ID']]['TEAM_HOME_ID'] is None:
                    enriched_game_list[game['GAME_ID']]['TEAM_HOME_ID'] = game['TEAM_ID']
                    enriched_game_list[game['GAME_ID']]['TEAM_HOME_NAME'] = game['TEAM_NAME']
                    enriched_game_list[game['GAME_ID']]['TEAM_HOME_ABBREVIATION'] = game['TEAM_ABBREVIATION']
                elif enriched_game_list[game['GAME_ID']]['TEAM_AWAY_ID'] is None:
                    enriched_game_list[game['GAME_ID']]['TEAM_AWAY_ID'] = game['TEAM_ID']
                    enriched_game_list[game['GAME_ID']]['TEAM_AWAY_NAME'] = game['TEAM_NAME']
                    enriched_game_list[game['GAME_ID']]['TEAM_AWAY_ABBREVIATION'] = game['TEAM_ABBREVIATION']
            else:
                season_type = None
                if game['SEASON_ID'].startswith('1'):
                    season_type = 'PreSeason'
                elif game['SEASON_ID'].startswith('2'):
                    season_type = 'RegularSeason'
                elif game['SEASON_ID'].startswith('3'):
                    season_type = 'AllStar'
                elif game['SEASON_ID'].startswith('4'):
                    season_type = 'PlayOff'
                elif game['SEASON_ID'].startswith('5'):
                    season_type = 'PlayIn'

                matchup_pattern = r'\b([A-Z]+) vs. ([A-Z]+)\b'
                matchup_alt_pattern = r'\b([A-Z]+) @ ([A-Z]+)\b'

                team_home_id = None
                team_away_id = None
                team_home_name = None
                team_away_name = None
                team_home_abbreviation = None
                team_away_abbreviation = None
                matchup = None
                if re.fullmatch(matchup_pattern, game['MATCHUP']):
                    matchup = game['MATCHUP']
                    team_home_id = game['TEAM_ID']
                    team_home_name = game['TEAM_NAME']
                    team_home_abbreviation = game['TEAM_ABBREVIATION']
                elif re.fullmatch(matchup_alt_pattern, game['MATCHUP']):
                    matchup_replacement = r'\2 vs. \1'
                    matchup = re.sub(matchup_alt_pattern, matchup_replacement, game['MATCHUP'])
                    team_away_id = game['TEAM_ID']
                    team_away_name = game['TEAM_NAME']
                    team_away_abbreviation = game['TEAM_ABBREVIATION']

                enriched_game_list[game['GAME_ID']] = {
                    'GAME_ID': game['GAME_ID'],
                    'GAME_DATE': game['GAME_DATE'],
                    'SEASON_ID': game['SEASON_ID'],
                    'SEASON_TYPE': season_type,
                    'SEASON_YEAR': season,
                    'MATCHUP': matchup,
                    'TEAM_HOME_ID': team_home_id,
                    'TEAM_HOME_NAME': team_home_name,
                    'TEAM_HOME_ABBREVIATION': team_home_abbreviation,
                    'TEAM_AWAY_ID': team_away_id,
                    'TEAM_AWAY_NAME': team_away_name,
                    'TEAM_AWAY_ABBREVIATION': team_away_abbreviation,
                    'HOME_BACK_TO_BACK': False,  # need to be computed with self.back_to_back_detection()
                    'AWAY_BACK_TO_BACK': False,  # need to be computed with self.back_to_back_detection()
                }
        return enriched_game_list

    def list_season_games(self, season=None, force_refresh=False):
        if not season:
            season = self.current_season

        print("[Games] List game for season: " + season)

        if season not in self.calendar or force_refresh:
            list_games = leaguegamefinder.LeagueGameFinder(season_nullable=season, league_id_nullable=LeagueIDNullable.nba)
            season_raw_game_df = list_games.get_data_frames()[0]
            season_games = self.enriched_season_game_list(season, season_raw_game_df)

            season_calendar_df = pd.DataFrame.from_dict(season_games.values())

            self.calendar[season] = season_calendar_df
            self.back_to_back_detection(season)
            self.save_calendar(season)

        return self.calendar[season]

    def get_box_score(self, game_id, game_info_df):
        players = Players()

        home_id = game_info_df['TEAM_HOME_ID']
        away_team_id = game_info_df['TEAM_AWAY_ID']
        home_abbreviation = game_info_df['TEAM_HOME_ABBREVIATION']
        away_abbreviation = game_info_df['TEAM_AWAY_ABBREVIATION']
        home_b2b = game_info_df['HOME_BACK_TO_BACK']
        away_b2b = game_info_df['AWAY_BACK_TO_BACK']
        if game_id not in self.box_scores:
            print("[Games] Retrieve box score for game: " + game_id)
            box_score = boxscoretraditionalv2.BoxScoreTraditionalV2(game_id=game_id)
            box_score_df = box_score.get_data_frames()[0]
            box_score_df = box_score_df.fillna(0)
            box_score_df = self.calculate_ttlf_score(box_score_df)

            box_score_df['GAME_DATE'] = game_info_df['GAME_DATE']
            box_score_df['SEASON'] = game_info_df['SEASON_YEAR']
            box_score_df['SEASON_TYPE'] = game_info_df['SEASON_TYPE']
            box_score_df['MATCHUP'] = game_info_df['MATCHUP']
            box_score_df['OPPONENT_TEAM_ID'] = box_score_df.apply(lambda player_box_score: away_team_id if player_box_score['TEAM_ID'] == home_id else home_id, axis=1)
            box_score_df['OPPONENT_ABBREVIATION'] = box_score_df.apply(lambda player_box_score: away_abbreviation if player_box_score['TEAM_ID'] == home_id else home_abbreviation, axis=1)
            box_score_df['HOME_AWAY'] = box_score_df.apply(lambda player_box_score: 'HOME' if player_box_score['TEAM_ID'] == home_id else 'AWAY', axis=1)
            box_score_df['PLAYER_POSITION'] = box_score_df.apply(lambda player_box_score: players.get_player_position(player_box_score['PLAYER_ID']), axis=1)
            box_score_df['BACK_TO_BACK'] = box_score_df.apply(lambda player_box_score: home_b2b if player_box_score['TEAM_ID'] == home_id else away_b2b, axis=1)

            box_score_df = box_score_df.drop(columns=['NICKNAME', 'START_POSITION', 'TEAM_CITY', 'FG_PCT', 'FG3_PCT', 'FT_PCT'])

            self.box_scores[game_id] = box_score_df

        return self.box_scores[game_id]

    def calculate_ttlf_score(self, box_score_df):
        box_score_df['TTFL_SCORE'] = \
            + box_score_df['PTS'] \
            + box_score_df['REB'] \
            + box_score_df['AST'] \
            + box_score_df['STL'] \
            + box_score_df['BLK'] \
            + 2 * box_score_df['FGM'] \
            + 2 * box_score_df['FG3M'] \
            + 2 * box_score_df['FTM'] \
            - box_score_df['TO'] \
            - box_score_df['FGA'] \
            - box_score_df['FG3A'] \
            - box_score_df['FTA']
        box_score_df["TTFL_SCORE"] = box_score_df["TTFL_SCORE"].fillna(0)
        return box_score_df

    def fetch_season_box_scores(self, season, force_refresh=False):
        if not season:
            season = self.current_season

        list_games_df = self.list_season_games(season, force_refresh)

        all_box_scores = []
        has_error = False
        has_new_row = False
        for i, game_df in list_games_df.iterrows():
            if has_new_row and i % self.buffer_size == 0:
                self.save_box_scores(season)
                has_new_row = False

            print("[Games] Loading in progress: " + str(i + 1) + " / " + str(len(list_games_df.index)))
            game_id = game_df['GAME_ID']
            if not force_refresh and game_id in self.box_scores:
                all_box_scores.append(self.box_scores[game_id])
            else:
                try:
                    box_score_df = self.get_box_score(game_id, game_df)
                    all_box_scores.append(box_score_df)
                    has_new_row = True
                except Exception as error:
                    has_error = True
                    print("[Error] Failed to retrieve data for game: " + game_id, file=sys.stderr)
                    print(error, file=sys.stderr)

        self.save_box_scores(season)

        return [pd.concat(all_box_scores), not has_error]

    def get_box_scores_for_players(self, player_id_list, before_day=None, season_type=None):
        if before_day is None:
            before_day = date.today().isoformat()
        else:
            date_object = datetime.strptime(before_day, "%m/%d/%Y")
            before_day = date_object.date().isoformat()

        print("[Games] Get box scores for today players : " + before_day)

        if not season_type:
            season_type = "RegularSeason"

        all_box_scores_df = pd.concat(self.box_scores.values())
        return all_box_scores_df[
            (all_box_scores_df['PLAYER_ID'].isin(player_id_list))
            & (all_box_scores_df['GAME_DATE'] < before_day)
            # To remove for early season
            #& (all_box_scores_df['SEASON_TYPE'] == season_type)
        ]
