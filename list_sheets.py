import gspread
from oauth2client.service_account import ServiceAccountCredentials
import config
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def list_all_sheets():
    creds_source = config.get_google_credentials()
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    
    if isinstance(creds_source, dict):
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_source, scope)
    else:
        creds = ServiceAccountCredentials.from_json_keyfile_name(creds_source, scope)
    
    client = gspread.authorize(creds)
    
    logger.info("Listing all spreadsheets accessible to this service account:")
    spreadsheets = client.openall()
    if not spreadsheets:
        logger.info("No spreadsheets found!")
        return

    for ss in spreadsheets:
        logger.info(f"Spreadsheet Name: '{ss.title}', ID: '{ss.id}'")
        for i, ws in enumerate(ss.worksheets()):
            rows = ws.get_all_values()
            logger.info(f"  - Worksheet {i}: '{ws.title}', ID: '{ws.id}', Rows: {len(rows)}")

if __name__ == "__main__":
    list_all_sheets()
