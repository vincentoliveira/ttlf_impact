# TTFL Lab Impact
#
# Google Drive
#
# Google Drive Manager

import os
import os.path
import gspread
import numpy as np
import pandas as pd

from datetime import datetime
from dotenv import load_dotenv
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


class GoogleDrive():
    def __init__(self):
        load_dotenv()
        self.api_key = os.environ.get('GOOGLE_API_KEY')
        self.gdrive_credentials_file = 'credentials.json'
        self.template_id = '1HsY1_Xs2A6oHxCNLL8ErpHmVB3dgOyijAAXkxvGqdQU'
        self.impact_filename = 'impact_{day}'
        self.data_sheet_name = 'impact_data'

    def copy_impact_template(self, day, weekly=False):
        SCOPES = ["https://www.googleapis.com/auth/drive",
                  "https://www.googleapis.com/auth/drive.metadata",
                  "https://www.googleapis.com/auth/spreadsheets"]
        credentials = service_account.Credentials.from_service_account_file(self.gdrive_credentials_file, scopes=SCOPES)

        try:
            drive_service = build("drive", "v3", credentials=credentials)

            filename = self.get_filename(day, weekly)
            body = { 'name': filename, 'copy_permissions': True }
            copy_response = drive_service.files().copy(fileId=self.template_id, body=body).execute()
            sheet_id = copy_response.get('id')

            permission = {
                'type': 'anyone',
                'role': 'writer',
            }
            drive_service.permissions().create(fileId=sheet_id, body=permission).execute()

            return sheet_id
        except HttpError as error:
            print(f"An error occurred: {error}")

    def write_impact_data(self, sheet_id, impact_table, metadata):
        gc = gspread.service_account(self.gdrive_credentials_file)
        sheet = gc.open_by_key(sheet_id)
        impact_sheet = sheet.worksheet('impact_data')
        metadata_sheet = sheet.worksheet('metadata')

        # load data
        impact_df = pd.DataFrame.from_records(impact_table)\
            .sort_values(['TTFL_PREDICTION_WITHOUT_IMPACT'], ascending=False)\
            .replace(np.nan, None)
        metadata_df = pd.DataFrame.from_records([metadata])

        impact_sheet.update([impact_df.columns.values.tolist()] + impact_df.values.tolist())
        metadata_sheet.update([metadata_df.columns.values.tolist()] + metadata_df.values.tolist())

    def get_filename(self, day, weekly = False):
        date_object = datetime.strptime(day, "%m/%d/%Y")
        return self.impact_filename.replace('{day}', date_object.strftime("%Y-%m-%d"))
