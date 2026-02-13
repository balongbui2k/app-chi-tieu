import gspread
from oauth2client.service_account import ServiceAccountCredentials
import config

def debug_target_sheet():
    print(f"Target Sheet Name: {config.GOOGLE_SHEET_NAME}")
    creds_source = config.get_google_credentials()
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    
    if isinstance(creds_source, dict):
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_source, scope)
    else:
        creds = ServiceAccountCredentials.from_json_keyfile_name(creds_source, scope)
    
    client = gspread.authorize(creds)
    
    try:
        ss = client.open(config.GOOGLE_SHEET_NAME)
        print(f"Opened spreadsheet: {ss.title} (ID: {ss.id})")
        ws = ss.sheet1
        print(f"Opened Worksheet: {ws.title}")
        rows = ws.get_all_values()
        print(f"Number of rows: {len(rows)}")
        if rows:
            print(f"Header: {rows[0]}")
            if len(rows) > 1:
                print(f"Last row: {rows[-1]}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_target_sheet()
