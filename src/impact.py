# TTFL Lab Impact
#
# Games
#
# Fetch Game Information

from src.singleton_meta import SingletonMeta
from datetime import datetime, timedelta
import pandas as pd

class Impact(metaclass=SingletonMeta):
    def __init__(self, impact_filename='databases/impact_{day}.xlsx'):
        self.predictions = {}
        self.impact_filename = impact_filename

    def save_impact(self, day, impact_table):
        date_object = datetime.strptime(day, "%m/%d/%Y")
        filename = self.impact_filename.replace('{day}', date_object.strftime("%Y_%m_%d"))
        print("Writing impact table file to: " + filename)
        impact_df = pd.DataFrame.from_records(impact_table).sort_values(['SEASON_AVG'], ascending=False)
        impact_df.to_excel(filename, index=False)

    def compute_impact(self, day, game_df, player_df, box_score_df):
        date_object = datetime.strptime(day, "%m/%d/%Y")
        ten_days_ago = (date_object - timedelta(days=10)).strftime("%Y-%m-%d")
        thirty_days_ago = (date_object - timedelta(days=30)).strftime("%Y-%m-%d")

        impact_table = []
        for i, player in player_df.iterrows():
            player_box_score = box_score_df[box_score_df['PLAYER_ID'] == player['PERSON_ID']]
            player_box_score = player_box_score.sort_values(['GAME_DATE'], ascending=False)
            last_ten_days_box_score = player_box_score[player_box_score['GAME_DATE'] >= ten_days_ago]
            last_thirty_days_box_score = player_box_score[player_box_score['GAME_DATE'] >= thirty_days_ago]
            player_id = player['PERSON_ID']
            player_name = player['DISPLAY_FIRST_LAST']
            season_average = player_box_score['TTFL_SCORE'].mean()
            last_ten_days_average = last_ten_days_box_score['TTFL_SCORE'].mean()
            last_thirty_days_average = last_thirty_days_box_score['TTFL_SCORE'].mean()
            last_30_nb_played = len(last_thirty_days_box_score)
            last_30_below_twenty = len(last_thirty_days_box_score[last_thirty_days_box_score['TTFL_SCORE'] < 20])
            last_30_between_twenty_and_thirty = len(last_thirty_days_box_score[last_thirty_days_box_score['TTFL_SCORE'].between(20, 29)])
            last_30_between_thirty_and_fourty = len(last_thirty_days_box_score[last_thirty_days_box_score['TTFL_SCORE'].between(30, 39)])
            last_30_above_fourty = len(last_thirty_days_box_score[last_thirty_days_box_score['TTFL_SCORE'] >= 40])
            match_up = game_df[game_df['TEAM_ID'] == player['TEAM_ID']]['MATCHUP'].values[0]
            last_game = player_box_score['TTFL_SCORE'].values[0] if len(player_box_score['TTFL_SCORE']) >= 1 else None
            last_2_game = player_box_score['TTFL_SCORE'].values[1] if len(player_box_score['TTFL_SCORE']) >= 2 else None
            last_3_game = player_box_score['TTFL_SCORE'].values[2] if len(player_box_score['TTFL_SCORE']) >= 3 else None
            last_4_game = player_box_score['TTFL_SCORE'].values[3] if len(player_box_score['TTFL_SCORE']) >= 4 else None

            impact_table.append({
                'PLAYER_ID': player_id,
                'PLAYER_NAME': player_name,
                'SEASON_AVG': season_average,
                '10_DAYS_AVG': last_ten_days_average,
                '30_DAYS_AVG': last_thirty_days_average,
                '30_DAYS_NB_PLAYED': last_30_nb_played,
                '30_DAYS_BELOW_20': last_30_below_twenty,
                '30_DAYS_20_30': last_30_between_twenty_and_thirty,
                '30_DAYS_30_40': last_30_between_thirty_and_fourty,
                '30_DAYS_ABOVE_40': last_30_above_fourty,
                'LAST_4_GAME': last_4_game,
                'LAST_3_GAME': last_3_game,
                'LAST_2_GAME': last_2_game,
                'LAST_GAME': last_game,
                'MATCHUP': match_up,
            })

        self.save_impact(day, impact_table)

        return impact_table
