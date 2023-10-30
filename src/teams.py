# TTFL Lab Impact
#
# Teams
#
# Fetch Team Information
from src.singleton_meta import SingletonMeta
from nba_api.stats.endpoints import teaminfocommon
import pandas as pd
import sys


class Teams(metaclass=SingletonMeta):
    def __init__(self, database_filename='databases/teams.xlsx'):
        self.teams = {}
        self.database_filename = database_filename

        # load initial database
        self.load_database()

    def load_database(self):
        try:
            existing_teams = pd.read_excel(self.database_filename, dtype='object')
            team_id_list = existing_teams['TEAM_ID'].unique().tolist()
            for team_id in team_id_list:
                self.teams[team_id] = existing_teams[existing_teams['TEAM_ID'] == team_id]
        except FileNotFoundError:
            print("Failed to load existing team database: File " + self.database_filename + " not found.",
                  file=sys.stderr)
        except Exception as e:
            print("Failed to load existing team database: " + str(e), file=sys.stderr)

    def save_database(self):
        print("Writing team database file to: " + self.database_filename)
        all_box_scores_df = pd.concat(self.teams.values())
        all_box_scores_df.to_excel(self.database_filename, index=False)

    def get_team_info(self, team_id):
        if team_id not in self.teams:
            print("[Team] Retrieve info for team: " + str(team_id))
            team_info = teaminfocommon.TeamInfoCommon(team_id=team_id)
            team_info_df = team_info.get_data_frames()[0]
            team_info_df = team_info_df.drop(columns=['W', 'L', 'PCT', 'CONF_RANK', 'DIV_RANK'])
            self.teams[team_id] = team_info_df

        return self.teams[team_id]

    def fetch_all_team_info(self, team_id_list):
        all_team_info = []
        has_error = False
        for i, team_id in enumerate(team_id_list):
            print("[Teams] Loading in progress: " + str(i + 1) + " / " + str(len(team_id_list)))
            if team_id in self.teams:
                all_team_info.append(self.teams[team_id])
                continue

            try:
                team_info = self.get_team_info(team_id)
                all_team_info.append(team_info)
            except Exception as error:
                has_error = True
                print("[Error] Failed to retrieve info for team: " + str(team_id), file=sys.stderr)
                print(error, file=sys.stderr)

        self.save_database()

        return [pd.concat(all_team_info), not has_error]

    def find_team_id_by_abbreviation(self, opponent_abbreviation):
        all_box_scores_df = pd.concat(self.teams.values())
        team = all_box_scores_df[all_box_scores_df['TEAM_ABBREVIATION'] == opponent_abbreviation]['TEAM_ID']
        return team.values[0] if len(team) >= 1 else None
