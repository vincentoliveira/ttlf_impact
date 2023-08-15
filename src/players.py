# TTFL Lab Impact
#
# Players
#
# Fetch Player Information
from src.singleton_meta import SingletonMeta
from nba_api.stats.endpoints import commonplayerinfo, commonteamroster
import pandas as pd
import sys

class Players(metaclass=SingletonMeta):
    def __init__(self, database_filename='databases/players.xlsx', buffer_size=256):
        self.players = {}
        self.database_filename = database_filename
        self.buffer_size = buffer_size

        # load initial database
        self.load_database()

    def load_database(self):
        try:
            existing_players = pd.read_excel(self.database_filename, dtype='object')
            player_id_list = existing_players['PERSON_ID'].unique().tolist()
            for player_id in player_id_list:
                self.players[player_id] = existing_players[existing_players['PERSON_ID'] == player_id]
        except FileNotFoundError:
            print("Failed to load existing player database: File " + self.database_filename + " not found.", file=sys.stderr)
        except Exception as e:
            print("Failed to load existing player database: " + str(e), file=sys.stderr)

    def save_database(self):
        print("Writing players database file to: " + self.database_filename)
        all_box_scores_df = pd.concat(self.players.values())
        all_box_scores_df.to_excel(self.database_filename, index=False)

    def get_player_info(self, player_id):
        if player_id not in self.players:
            print("[Player] Retrieve info for player: " + str(player_id))
            player_info = commonplayerinfo.CommonPlayerInfo(player_id=player_id)
            player_info_df = player_info.get_data_frames()[0]
            self.players[player_id] = player_info_df

        return self.players[player_id]

    def get_roster_by_team_id(self, team_id):
        print("[Player] Retrieve roster for team: " + str(team_id))
        roster_info = commonteamroster.CommonTeamRoster(team_id=team_id)
        roster_info_df = roster_info.get_data_frames()[0]
        return roster_info_df

    def fetch_all_player_info(self, player_id_list):
        all_player_info = []
        has_error = False
        has_new_row = False
        for i, player_id in enumerate(player_id_list):
            print("[Players] Loading in progress: " + str(i + 1) + " / " + str(len(player_id_list)))
            if player_id in self.players:
                all_player_info.append(self.players[player_id])
            else:
                try:
                    player_info = self.get_player_info(player_id)
                    all_player_info.append(player_info)
                    has_new_row = True
                except Exception as error:
                    has_error = True
                    print("[Error] Failed to retrieve info for players: " + str(player_id), file=sys.stderr)
                    print(error, file=sys.stderr)

            if has_new_row and i % self.buffer_size == 0:
                self.save_database()
                has_new_row = False

        self.save_database()

        return [pd.concat(all_player_info), not has_error]

    def fetch_player_by_teams(self, team_id_list):
        all_player_info = []
        has_change = False
        for i, team_id in enumerate(team_id_list):
            print("[Players] Loading in progress: " + str(i + 1) + " / " + str(len(team_id_list)))
            roster_df = self.get_roster_by_team_id(team_id)
            for player_id in roster_df['PLAYER_ID'].to_list():
                player = self.players[player_id]
                initial_team_id = player['TEAM_ID'].values[0]
                if player is None:
                    print("[Players] Player " + player_id + " not found.")
                    player = self.get_player_info(player_id)
                    has_change = True
                elif initial_team_id != team_id:
                    print("[Players] Player " + str(player_id) + " found in the wrong team (" + str(initial_team_id) + " instead of " + str(team_id) + ")")
                    player['TEAM_ID'] = team_id
                    has_change = True

                all_player_info.append(player)

        if has_change:
            self.save_database()

        return pd.concat(all_player_info)
