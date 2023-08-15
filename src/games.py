# TTFL Lab Impact
#
# Games
#
# Fetch Game Information

from src.singleton_meta import SingletonMeta
from nba_api.stats.endpoints import leaguegamefinder, boxscoretraditionalv2
from nba_api.stats.library.parameters import LeagueIDNullable
import re
import pandas as pd
import sys
from datetime import date, datetime

class Games(metaclass=SingletonMeta):
    def __init__(self, current_season='2022-23', database_filename='databases/box_scores.xlsx', buffer_size=256):
        self.box_scores = {}
        self.current_season = current_season
        self.database_filename = database_filename
        self.buffer_size = buffer_size

        # load initial database
        self.load_database()

    def load_database(self):
        try:
            existing_box_scores = pd.read_excel(self.database_filename, dtype='object')
            game_id_list = existing_box_scores['GAME_ID'].unique().tolist()
            for game_id in game_id_list:
                self.box_scores[game_id] = existing_box_scores[existing_box_scores['GAME_ID'] == game_id]
        except FileNotFoundError:
            print("Failed to load existing box score database: File " + self.database_filename + " not found.", file=sys.stderr)
        except Exception as e:
            print("Failed to load existing box score database: " + str(e), file=sys.stderr)

    def save_database(self):
        print("Writing box score database file to: " + self.database_filename)
        all_box_scores_df = pd.concat(self.box_scores.values())
        all_box_scores_df.to_excel(self.database_filename, index=False)

    def list_daily_games(self, day=None, league=LeagueIDNullable.nba):
        if not day:
            day = date.today().strftime("%d/%m/%Y")

        print("[Game] List game for this day: " + day)
        list_games = leaguegamefinder.LeagueGameFinder(
            date_from_nullable=day,
            date_to_nullable=day,
            league_id_nullable=league
        )
        list_games_df = list_games.get_data_frames()[0]

        return list_games_df

    def list_season_games(self, season=None):
        if not season:
            season = self.current_season

        print("[Game] List game for season: " + season)
        list_games = leaguegamefinder.LeagueGameFinder(season_nullable=season)
        list_games_df = list_games.get_data_frames()[0]

        return list_games_df

    def get_box_score(self, game_id, game_df):
        if game_id not in self.box_scores:
            print("[Game] Retrieve box score for game: " + game_id)
            box_score = boxscoretraditionalv2.BoxScoreTraditionalV2(game_id=game_id)
            box_score_df = box_score.get_data_frames()[0]
            box_score_df = box_score_df.drop(columns=['TEAM_ABBREVIATION', 'TEAM_CITY', 'PLAYER_NAME', 'NICKNAME', 'START_POSITION'])
            box_score_df = box_score_df.fillna(0)
            box_score_df = self.calculate_ttlf_score(box_score_df)

            box_score_df['GAME_DATE'] = game_df['GAME_DATE']

            matchup = None
            matchup_alt = None

            matchup_pattern = r'\b([A-Z]+) vs. ([A-Z]+)\b'
            matchup_alt_pattern = r'\b([A-Z]+) @ ([A-Z]+)\b'

            if re.fullmatch(matchup_pattern, game_df['MATCHUP']):
                matchup_alt_replacement = r'\2 @ \1'
                matchup = game_df['MATCHUP']
                matchup_alt = re.sub(matchup_pattern, matchup_alt_replacement, game_df['MATCHUP'])
            elif re.fullmatch(matchup_alt_pattern, game_df['MATCHUP']):
                matchup_replacement = r'\2 vs. \1'
                matchup = re.sub(matchup_alt_pattern, matchup_replacement, game_df['MATCHUP'])
                matchup_alt = game_df['MATCHUP']

            box_score_df['MATCHUP'] = matchup
            box_score_df['MATCHUP_ALT'] = matchup_alt

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

    def fetch_season_box_scores(self, season):
        if not season:
            season = self.current_season

        list_games_df = self.list_season_games(season)

        all_box_scores = []
        has_error = False
        has_new_row = False
        for i, game_df in list_games_df.iterrows():
            print("[Games] Loading in progress: " + str(i + 1) + " / " + str(len(list_games_df.index)))
            game_id = game_df['GAME_ID']
            if game_id in self.box_scores:
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

            if has_new_row and i % self.buffer_size == 0:
                self.save_database()
                has_new_row = False

        self.save_database()

        return [pd.concat(all_box_scores), not has_error]

    def get_box_scores_for_players(self, player_id_list, before_day=None, season_type=None):
        if before_day is None:
            before_day = date.today().isoformat()
        else:
            date_object = datetime.strptime(before_day, "%m/%d/%Y")
            before_day = date_object.date().isoformat()

        game_prefix = ''
        if season_type == 'SR':
            game_prefix = '002'
        elif season_type == 'PO':
            game_prefix = '004'

        all_box_scores_df = pd.concat(self.box_scores.values())
        return all_box_scores_df[
            (all_box_scores_df['PLAYER_ID'].isin(player_id_list))
            & (all_box_scores_df['GAME_DATE'] < before_day)
            & (all_box_scores_df['GAME_ID'].str.startswith(game_prefix))
        ]
