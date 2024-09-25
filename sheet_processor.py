import gspread
from datetime import date
from gspread.utils import ValueInputOption
from google.oauth2.service_account import Credentials

# 인증 및 Google Sheets API와 연결
def connect_to_gsheet(json_keyfile_path, spreadsheet_id):
    scope = ["https://spreadsheets.google.com/feeds", 'https://www.googleapis.com/auth/spreadsheets',
             "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]

    creds = Credentials.from_service_account_file(json_keyfile_path, scopes=scope)
    client = gspread.authorize(creds)
    spreadsheet = client.open_by_key(spreadsheet_id)

    return spreadsheet

def insert_column_after_last_but_one(spreadsheet, worksheet_id):
    worksheet = spreadsheet.get_worksheet_by_id(worksheet_id)

    insert_index = 6

    today = date.today().strftime("%Y-%m-%d")
    values = [[today]]

    worksheet.insert_cols(
        values,
        col=insert_index,
        value_input_option=ValueInputOption.user_entered,
        inherit_from_before=True
    )
