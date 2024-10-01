# TTFL Lab Impact
#
# Discord

import os
import requests
from dotenv import load_dotenv


class Discord:
    def __init__(self):
        load_dotenv()
        self.webhook_url = os.environ.get('DISCORD_WEBHOOK_URL')

    def send_google_spreadsheets(self, spreadsheet_url):
        data = {
            "content": "Impact du jour: " + spreadsheet_url,
            "username": "Lucienne"
        }
        result = requests.post(self.webhook_url, json=data)
        result.raise_for_status()
