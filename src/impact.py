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
            player_id = player['PERSON_ID']
            team_id = player['TEAM_ID']
            game_id = game_df[game_df['TEAM_ID'] == player['TEAM_ID']]['GAME_ID'].values[0]

            team_box_score_df = box_score_df[box_score_df['TEAM_ID'] == team_id].sort_values(['GAME_DATE'], ascending=False)
            team_last_four_game_dates = team_box_score_df['GAME_DATE'].unique().tolist()
            player_box_score = box_score_df[box_score_df['PLAYER_ID'] == player_id].sort_values(['GAME_DATE'], ascending=False)
            last_ten_days_box_score = player_box_score[player_box_score['GAME_DATE'] >= ten_days_ago]
            last_thirty_days_box_score = player_box_score[player_box_score['GAME_DATE'] >= thirty_days_ago]

            # General information
            player_name = player['DISPLAY_FIRST_LAST']
            last_game_date_tomorrow = (datetime.strptime(player_box_score['GAME_DATE'].values[0], "%Y-%m-%d") + timedelta(days=1)).strftime("%m/%d/%Y") \
                if len(player_box_score['TTFL_SCORE']) >= 1 else False
            is_back_to_back = last_game_date_tomorrow and last_game_date_tomorrow == day

            # Average
            season_average = player_box_score['TTFL_SCORE'].mean()
            last_ten_days_average = last_ten_days_box_score['TTFL_SCORE'].mean()
            last_thirty_days_average = last_thirty_days_box_score['TTFL_SCORE'].mean()

            # Trends - 30 days
            last_30_nb_played = len(last_thirty_days_box_score)
            last_30_below_twenty = len(last_thirty_days_box_score[last_thirty_days_box_score['TTFL_SCORE'] < 20])
            last_30_between_twenty_and_thirty = len(last_thirty_days_box_score[last_thirty_days_box_score['TTFL_SCORE'].between(20, 29)])
            last_30_between_thirty_and_fourty = len(last_thirty_days_box_score[last_thirty_days_box_score['TTFL_SCORE'].between(30, 39)])
            last_30_above_fourty = len(last_thirty_days_box_score[last_thirty_days_box_score['TTFL_SCORE'] >= 40])

            # Trends - Last 4 games
            last_game_box_score = player_box_score[player_box_score['GAME_DATE'] == team_last_four_game_dates[0]] \
                if len(team_last_four_game_dates) >= 1 else None
            last_2_game_box_score = player_box_score[player_box_score['GAME_DATE'] == team_last_four_game_dates[1]] \
                if len(team_last_four_game_dates) >= 2 else None
            last_3_game_box_score = player_box_score[player_box_score['GAME_DATE'] == team_last_four_game_dates[2]] \
                if len(team_last_four_game_dates) >= 3 else None
            last_4_game_box_score = player_box_score[player_box_score['GAME_DATE'] == team_last_four_game_dates[3]] \
                if len(team_last_four_game_dates) >= 4 else None
            last_game = last_game_box_score['TTFL_SCORE'].values[0] if last_game_box_score is not None and len(last_game_box_score['TTFL_SCORE']) >= 1 else None
            last_2_game = last_2_game_box_score['TTFL_SCORE'].values[0] \
                if last_2_game_box_score is not None and len(last_2_game_box_score['TTFL_SCORE']) >= 1 else None
            last_3_game = last_3_game_box_score['TTFL_SCORE'].values[0] \
                if last_3_game_box_score is not None and len(last_3_game_box_score['TTFL_SCORE']) >= 1 else None
            last_4_game = last_4_game_box_score['TTFL_SCORE'].values[0] \
                if last_4_game_box_score is not None and len(last_4_game_box_score['TTFL_SCORE']) >= 1 else None

            # Match up
            match_up = game_df[game_df['TEAM_ID'] == player['TEAM_ID']]['MATCHUP'].values[0]
            opponent_team_id = game_df[(game_df['GAME_ID'] == game_id) & (game_df['TEAM_ID'] != player['TEAM_ID'])]['TEAM_ID'].values[0]
            opponent_box_score_df = box_score_df[box_score_df['TEAM_ID'] == opponent_team_id].sort_values(['GAME_DATE'], ascending=False)
            opponent_last_game_date = opponent_box_score_df['GAME_DATE'].unique().tolist()
            last_game_date_tomorrow = (datetime.strptime(opponent_last_game_date[0], "%Y-%m-%d") + timedelta(days=1)).strftime("%m/%d/%Y") if len(opponent_last_game_date) >= 1 else False
            opponent_back_to_back = last_game_date_tomorrow == day

            # Match Up History
            match_up_history_df = player_box_score[player_box_score['OPPONENT_TEAM_ID'] == opponent_team_id]
            last_match_up = match_up_history_df['TTFL_SCORE'].values[0] \
                if len(match_up_history_df['TTFL_SCORE']) >= 1 else None
            last_2_match_up = match_up_history_df['TTFL_SCORE'].values[1] \
                if len(match_up_history_df['TTFL_SCORE']) >= 2 else None
            last_3_match_up = match_up_history_df['TTFL_SCORE'].values[2] \
                if len(match_up_history_df['TTFL_SCORE']) >= 3 else None

            impact_table.append({
                'PLAYER_ID': player_id,
                'PLAYER_NAME': player_name,
                'BACK_TO_BACK': is_back_to_back,
                'SEASON_AVG': season_average,
                '30_DAYS_AVG': last_thirty_days_average,
                '10_DAYS_AVG': last_ten_days_average,
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
                'OPPONENT_B2B': opponent_back_to_back,
                'LAST_MATCHUP': last_match_up,
                'LAST_2_MATCHUP': last_2_match_up,
                'LAST_3_MATCHUP': last_3_match_up,
            })

        self.save_impact(day, impact_table)

        return impact_table
