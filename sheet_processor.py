import gspread
from google.oauth2.service_account import Credentials

# 인증 및 Google Sheets API와 연결
def connect_to_gsheet(json_keyfile_path, spreadsheet_id):
    scope = ["https://spreadsheets.google.com/feeds", 'https://www.googleapis.com/auth/spreadsheets',
             "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]

    creds = Credentials.from_service_account_file(json_keyfile_path, scopes=scope)
    client = gspread.authorize(creds)
    spreadsheet = client.open_by_key(spreadsheet_id)

    return spreadsheet