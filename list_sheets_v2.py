import gspread
from oauth2client.service_account import ServiceAccountCredentials
import config

def list_all_sheets():
    print("Starting listing...")
    creds_source = config.get_google_credentials()
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    
    if isinstance(creds_source, dict):
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_source, scope)
    else:
        creds = ServiceAccountCredentials.from_json_keyfile_name(creds_source, scope)
    
    client = gspread.authorize(creds)
    
    spreadsheets = client.openall()
    print(f"Found {len(spreadsheets)} spreadsheets.")

    for ss in spreadsheets:
        print(f"Spreadsheet: '{ss.title}' (ID: {ss.id})")
        for i, ws in enumerate(ss.worksheets()):
            rows = ws.get_all_values()
            print(f"  - Worksheet {i}: '{ws.title}' (Rows: {len(rows)})")
            if rows:
                print(f"    Headers: {rows[0]}")

if __name__ == "__main__":
    try:
        list_all_sheets()
    except Exception as e:
        print(f"Error: {e}")
