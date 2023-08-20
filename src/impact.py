# TTFL Lab Impact
#
# Games
#
# Fetch Game Information

from src.singleton_meta import SingletonMeta
from datetime import datetime, timedelta
import pandas as pd
import sys

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

    def compute_team_position_impact(self, game_df, box_score_df):
        home_teams = game_df['TEAM_HOME_ID'].unique().tolist()
        away_teams = game_df['TEAM_AWAY_ID'].unique().tolist()
        teams = home_teams + away_teams

        team_impact_table = {}
        for team_id in teams:
            opponent_box_scores = box_score_df[(box_score_df['OPPONENT_TEAM_ID'] == team_id) & (box_score_df['MIN'] != 0)]
            position_impact_table = opponent_box_scores.groupby(['PLAYER_POSITION'])['TTFL_SCORE'].mean()
            team_impact_table[team_id] = position_impact_table

        return team_impact_table

    def get_position_short(self, position):
        if position == 'Guard':
            return 'G'
        elif position == 'Guard-Forward':
            return 'G-F'
        elif position == 'Forward-Guard':
            return 'F-G'
        elif position == 'Forward':
            return 'F'
        elif position == 'Forward-Center':
            return 'F-C'
        elif position == 'Center-Forward':
            return 'C-F'
        elif position == 'Center':
            return 'C'

    def get_team_position_score(self, position, team_score):
        if position == 'Guard':
            guard_score = team_score['Guard']
            guard_forward_score = team_score['Guard-Forward'] if 'Guard-Forward' in team_score else team_score['Guard']
            forward_guard_score = team_score['Forward-Guard'] if 'Forward-Guard' in team_score else team_score['Forward']
            return 0.6 * guard_score \
                + 0.3 * guard_forward_score \
                + 0.1 * forward_guard_score
        elif position == 'Guard-Forward':
            guard_score = team_score['Guard']
            guard_forward_score = team_score['Guard-Forward'] if 'Guard-Forward' in team_score else team_score['Guard']
            forward_guard_score = team_score['Forward-Guard'] if 'Forward-Guard' in team_score else team_score['Forward']
            forward_score = team_score['Forward']
            return 0.4 * guard_forward_score \
                + 0.3 * guard_score \
                + 0.2 * forward_guard_score \
                + 0.1 * forward_score
        elif position == 'Forward-Guard':
            guard_score = team_score['Guard']
            guard_forward_score = team_score['Guard-Forward'] if 'Guard-Forward' in team_score else team_score['Guard']
            forward_guard_score = team_score['Forward-Guard'] if 'Forward-Guard' in team_score else team_score['Forward']
            forward_score = team_score['Forward']
            return 0.4 * forward_guard_score \
                + 0.3 * forward_score \
                + 0.2 * guard_forward_score \
                + 0.1 * guard_score
        elif position == 'Forward':
            guard_forward_score = team_score['Guard-Forward'] if 'Guard-Forward' in team_score else team_score['Guard']
            forward_guard_score = team_score['Forward-Guard'] if 'Forward-Guard' in team_score else team_score['Forward']
            forward_score = team_score['Forward']
            forward_center_score = team_score['Forward-Center'] if 'Forward-Center' in team_score else team_score['Forward']
            center_forward_score = team_score['Center-Forward'] if 'Center-Forward' in team_score else team_score['Center']
            return 0.4 * forward_score \
                + 0.2 * forward_guard_score \
                + 0.2 * forward_center_score \
                + 0.1 * guard_forward_score \
                + 0.1 * center_forward_score
        elif position == 'Forward-Center':
            forward_score = team_score['Forward']
            forward_center_score = team_score['Forward-Center'] if 'Forward-Center' in team_score else team_score['Forward']
            center_forward_score = team_score['Center-Forward'] if 'Center-Forward' in team_score else team_score['Center']
            center_score = team_score['Center']
            return 0.4 * forward_center_score \
                + 0.3 * forward_score \
                + 0.2 * center_forward_score \
                + 0.1 * center_score
        elif position == 'Center-Forward':
            forward_score = team_score['Forward']
            forward_center_score = team_score['Forward-Center'] if 'Forward-Center' in team_score else team_score['Forward']
            center_forward_score = team_score['Center-Forward'] if 'Center-Forward' in team_score else team_score['Center']
            center_score = team_score['Center']
            return 0.4 * center_forward_score \
                + 0.3 * center_score \
                + 0.2 * forward_center_score \
                + 0.1 * forward_score
        elif position == 'Center':
            forward_center_score = team_score['Forward-Center'] if 'Forward-Center' in team_score else team_score['Forward']
            center_forward_score = team_score['Center-Forward'] if 'Center-Forward' in team_score else team_score['Center']
            center_score = team_score['Center']
            return 0.6 * center_score \
                + 0.3 * center_forward_score \
                + 0.1 * forward_center_score

    def compute_impact(self, day, season, game_df, player_df, box_score_df):
        date_object = datetime.strptime(day, "%m/%d/%Y")
        ten_days_ago = (date_object - timedelta(days=10)).strftime("%Y-%m-%d")
        thirty_days_ago = (date_object - timedelta(days=30)).strftime("%Y-%m-%d")

        home_teams = game_df['TEAM_HOME_ID'].unique().tolist()
        away_teams = game_df['TEAM_AWAY_ID'].unique().tolist()

        print("[Impact] Calculate impact: " + day)

        team_position_impact_table = self.compute_team_position_impact(game_df, box_score_df)
        played_game_box_score_df = box_score_df[box_score_df['MIN'] != 0]
        global_position_impact_table = played_game_box_score_df.groupby(['PLAYER_POSITION'])['TTFL_SCORE'].mean()

        impact_table = []
        for i, player in player_df.iterrows():
            player_id = player['PERSON_ID']
            team_id = player['TEAM_ID']

            this_game_df = None
            this_game_is_home = True
            opponent_team_id = None
            opponent_team_abbreviation = None
            if player['TEAM_ID'] in home_teams:
                this_game_df = game_df[game_df['TEAM_HOME_ID'] == player['TEAM_ID']].iloc[0]
                opponent_team_id = this_game_df['TEAM_AWAY_ID']
                opponent_team_abbreviation = this_game_df['TEAM_AWAY_ABBREVIATION']
                this_game_is_home = True
            elif player['TEAM_ID'] in away_teams:
                this_game_df = game_df[game_df['TEAM_AWAY_ID'] == player['TEAM_ID']].iloc[0]
                opponent_team_id = this_game_df['TEAM_HOME_ID']
                opponent_team_abbreviation = this_game_df['TEAM_HOME_ABBREVIATION']
                this_game_is_home = False
            else:
                print('[Impact] Error: team " + " do not play today', file=sys.stderr)
                continue

            team_box_score_df = box_score_df[box_score_df['TEAM_ID'] == team_id].sort_values(['GAME_DATE'], ascending=False)
            team_last_four_game_dates = team_box_score_df['GAME_DATE'].unique().tolist()
            player_box_score = box_score_df[box_score_df['PLAYER_ID'] == player_id].sort_values(['GAME_DATE'], ascending=False)

            # General information
            player_name = player['FIRST_NAME'] + " " + player['LAST_NAME']
            last_game_date_tomorrow = (datetime.strptime(player_box_score['GAME_DATE'].values[0], "%Y-%m-%d") + timedelta(days=1)).strftime("%m/%d/%Y") \
                if len(player_box_score['TTFL_SCORE']) >= 1 else False
            is_back_to_back = last_game_date_tomorrow and last_game_date_tomorrow == day

            # Average
            season_box_score = player_box_score[(player_box_score['SEASON'] == season)
                                                & (player_box_score['SEASON_TYPE'] == 'RegularSeason')
                                                & (player_box_score['MIN'] != 0)]
            last_ten_days_box_score = season_box_score[season_box_score['GAME_DATE'] >= ten_days_ago]
            last_thirty_days_box_score = season_box_score[season_box_score['GAME_DATE'] >= thirty_days_ago]
            season_average = season_box_score['TTFL_SCORE'].mean()
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
            match_up = this_game_df['MATCHUP']
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

            # Impact Position
            player_position = player['POSITION']
            player_position_short = self.get_position_short(player_position)
            opponent_position_score_table = team_position_impact_table[opponent_team_id]
            opponent_position_score = self.get_team_position_score(player_position, opponent_position_score_table)
            global_position_score = global_position_impact_table[player_position]
            opponent_position_impact = opponent_position_score - global_position_score

            # Impact Home Away
            player_home_away = "Home" if this_game_is_home else "Away"
            home_box_score = season_box_score[season_box_score['HOME_AWAY'] == 'HOME']
            away_box_score = season_box_score[season_box_score['HOME_AWAY'] == 'AWAY']
            home_average = home_box_score['TTFL_SCORE'].mean()
            away_average = away_box_score['TTFL_SCORE'].mean()
            home_away_impact = home_average - season_average if this_game_is_home else away_average - season_average

            # Impact Back to Back
            player_b2b_impact = None
            nb_b2b_played = None
            if is_back_to_back:
                player_b2b_box_score = season_box_score[season_box_score['BACK_TO_BACK']]
                player_b2b_average = player_b2b_box_score['TTFL_SCORE'].mean()
                player_b2b_impact = player_b2b_average - season_average
                nb_b2b_played = len(player_b2b_box_score.index)

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
                'LAST_3_MATCHUP': last_3_match_up,
                'LAST_2_MATCHUP': last_2_match_up,
                'LAST_MATCHUP': last_match_up,
                'PLAYER_POSITION': player_position_short + " vs. " + opponent_team_abbreviation,
                'POSITION_IMPACT': opponent_position_impact,
                'HOME_AWAY': player_home_away,
                'HOME_AVG': home_average,
                'AWAY_AVG': away_average,
                'HOME_AWAY_IMPACT': home_away_impact,
                'BACK_TO_BACK_IMPACT': player_b2b_impact,
                'NB_BACK_TO_BACK_PLAYED': nb_b2b_played,
            })

        self.save_impact(day, impact_table)

        return impact_table
