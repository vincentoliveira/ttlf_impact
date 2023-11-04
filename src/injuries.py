# TTFL Lab Impact
#
# Injuries
#
# Fetch Injury Report

from src.singleton_meta import SingletonMeta
from src.players import Players
from bs4 import BeautifulSoup
import requests


def compute_status(status, comment):
    if status == "Out":
        return "Out"

    lower_comment = comment.lower()
    if "questionable" in lower_comment:
        return "Questionable"
    elif "probable" in lower_comment:
        return "Probable"
    elif "doubt" in lower_comment:
        return "Doubtful"

    return "Questionable"


class Injuries(metaclass=SingletonMeta):
    def __init__(self):
        self.injury_report = []

    def load_injury_report(self):
        if len(self.injury_report) > 0:
            return self.injury_report

        injuries_url = "https://www.espn.com/nba/injuries"
        injuries_headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
        }
        injuries_response = requests.get(injuries_url, headers=injuries_headers)

        if injuries_response.status_code == 200:
            players = Players()
            self.injury_report = []

            soup = BeautifulSoup(injuries_response.text, 'html.parser')
            table_tr_elements = soup.find_all(class_="Table__TR")
            for element in table_tr_elements:
                name_cell = element.find(class_="col-name")
                status_cell = element.find(class_="col-stat")
                comment_cell = element.find(class_="col-desc")
                if name_cell is None or status_cell is None:
                    continue

                name = name_cell.get_text()
                player_id = players.get_player_id_by_name(name)
                if player_id is None:
                    print('[IR] Cannot find id of: ' + name)

                row_status = status_cell.get_text()
                comment = comment_cell.get_text()
                status = compute_status(row_status, comment)

                self.injury_report.append({
                    'PLAYER_ID': player_id,
                    'PLAYER_NAME': name,
                    'IR_STATUS': status,
                    'IR_COMMENT': comment,
                    'EXCLUDE_LIST': 'Out' if status == 'Out' else '',
                })
            return self.injury_report
        else:
            print('[IR] Failed to load injury report.')
            return []
