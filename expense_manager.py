import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from datetime import datetime, date, timedelta
import config
from categories import classify_expense
import logging
import unicodedata

logger = logging.getLogger(__name__)

class ExpenseManager:
    def __init__(self):
        self._client = None
        self._sheet = None
        self._connect_to_sheets()

    def _connect_to_sheets(self):
        """Connect to Google Sheets API."""
        creds_source = config.get_google_credentials()
        
        if not creds_source:
            logger.error("❌ No Google Credentials found!")
            return

        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        
        try:
            if isinstance(creds_source, dict):
                # Load from dict (Env Var)
                creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_source, scope)
            else:
                # Load from file path (Local)
                creds = ServiceAccountCredentials.from_json_keyfile_name(creds_source, scope)

            self._client = gspread.authorize(creds)
            
            # Open the spreadsheet
            spreadsheet = self._client.open(config.GOOGLE_SHEET_NAME)
            
            # Default to current month's sheet immediately
            now = datetime.now()
            self._sheet = self._get_or_create_worksheet(now, spreadsheet)
            
            # (Optional) If the default 'Sheet1' still exists and is empty, we could delete it, 
            # but usually it's safer to just leave it and work in the new monthly sheets.
                
        except Exception as e:
            logger.error(f"Google Sheets Connection Error: {e}")

    def _get_worksheet_name(self, date_obj):
        """Format worksheet name as '[Spreadsheet Name] mm/yyyy'."""
        return f"{config.GOOGLE_SHEET_NAME} {date_obj.strftime('%m/%Y')}"

    def _get_or_create_worksheet(self, date_obj, spreadsheet=None):
        """Get or create a worksheet for the given month."""
        if spreadsheet is None:
            if not self._client: self._connect_to_sheets()
            spreadsheet = self._client.open(config.GOOGLE_SHEET_NAME)
            
        try:
            worksheet = spreadsheet.worksheet(ws_name)
            # Check if header needs update (legacy 'Ngày' -> 'Ngày hôm nay')
            first_row = worksheet.row_values(1)
            if len(first_row) > 1 and first_row[1] == "Ngày":
                worksheet.update_cell(1, 2, "Ngày hôm nay")
        except gspread.exceptions.WorksheetNotFound:
            # Create new worksheet for the month
            worksheet = spreadsheet.add_worksheet(title=ws_name, rows="1000", cols="15")
            # Headers (Using 'Ngày hôm nay')
            worksheet.append_row(["ID", "Ngày hôm nay", "Giờ", "Người", "Danh mục", "Số tiền", "Mô tả"])
            
            # Add Total Summary formula in K1:L1
            try:
                worksheet.update_acell('K1', 'TỔNG CHI TIÊU:')
                worksheet.update_acell('L1', '=SUM(F2:F)')
                # Basic formatting for the header
                worksheet.format("A1:G1", {"textFormat": {"bold": True}, "backgroundColor": {"red": 0.9, "green": 0.9, "blue": 0.9}})
            except Exception as e:
                logger.warning(f"Could not format sheet: {e}")
                
        return worksheet

    def add_expense(self, amount, description, person="Bản thân", date=None):
        """Add a new expense record to Google Sheets."""
        if not self._sheet: self._connect_to_sheets()
        
        if date is None:
            date = datetime.now()
        
        # Ensure we are using the correct sheet for this month
        target_sheet = self._get_or_create_worksheet(date)
        
        category = classify_expense(description)
        
        # Format timestamps
        day_str = date.strftime("%Y-%m-%d")
        time_str = date.strftime("%H:%M:%S")
        expense_id = int(datetime.timestamp(datetime.now()) * 1000)

        # Row data (Removed month/year columns)
        row = [
            str(expense_id), day_str, time_str, person, category, amount, description
        ]
        
        try:
            # Use table_range='A1' to force appending from column A, even if there's data in K1
            target_sheet.append_row(row, table_range='A1')
            self._sheet = target_sheet # Update active sheet
            return {
                "ID": expense_id,
                "Ngày": day_str,
                "Người": person,
                "Danh mục": category,
                "Số tiền": amount,
                "Mô tả": description
            }
        except Exception as e:
            logger.error(f"Error adding row: {e}")
            # Try reconnecting once
            self._connect_to_sheets()
            self._sheet.append_row(row)
            return {
                "ID": expense_id,
                "Ngày": day_str,
                "Người": person,
                "Danh mục": category,
                "Số tiền": amount,
                "Mô tả": description
            }

    def get_expenses(self, start_date=None, end_date=None, person=None):
        """Retrieve expenses across monthly worksheets."""
        if not self._client: self._connect_to_sheets()
        
        try:
            spreadsheet = self._client.open(config.GOOGLE_SHEET_NAME)
            all_data = []
            final_header = ["ID", "Ngày", "Giờ", "Người", "Danh mục", "Số tiền", "Mô tả"]
            
            # Determine which worksheets to read
            target_worksheets = []
            if start_date and end_date:
                # Collect months between start and end
                curr = start_date
                while curr <= end_date:
                    name = self._get_worksheet_name(curr)
                    if name not in [ws.title for ws in target_worksheets]:
                        try:
                            target_worksheets.append(spreadsheet.worksheet(name))
                        except: pass
                    # Next month
                    if curr.month == 12: curr = curr.replace(year=curr.year+1, month=1)
                    else: curr = curr.replace(month=curr.month+1)
            else:
                # No specific range, try current month or all sheets matching the prefix in config
                prefix = config.GOOGLE_SHEET_NAME
                try:
                    target_worksheets.append(spreadsheet.worksheet(self._get_worksheet_name(datetime.now())))
                except:
                    # Fallback to all sheets starting with the config name
                    for ws in spreadsheet.worksheets():
                        if ws.title.startswith(prefix):
                            target_worksheets.append(ws)

            if not target_worksheets:
                return pd.DataFrame()

            for ws in target_worksheets:
                rows = ws.get_all_values()
                if len(rows) > 1:
                    raw_header = [str(h).strip() for h in rows[0]]
                    df_temp = pd.DataFrame(rows[1:], columns=raw_header)
                    all_data.append(df_temp)
            
            if not all_data:
                return pd.DataFrame()
                
            df = pd.concat(all_data, ignore_index=True)
            
            # Normalize headers to NFC and lowercase for comparison
            def normalize_str(s):
                if not s: return ""
                return unicodedata.normalize('NFC', str(s)).strip().lower()

            raw_header = [str(h).strip() for h in rows[0]]
            normalized_header = [normalize_str(h) for h in raw_header]
            data = rows[1:]

            # Map normalized headers to original ones
            header_map = {normalize_str(h): h for h in raw_header}
            
            # Find columns using normalized names
            # Prioritize exact match, then fallback to common variations
            date_col = header_map.get("ngày hôm nay") or header_map.get("ngày") or header_map.get("date") or next((h for h in raw_header if "ngày" in normalize_str(h)), None)
            amt_col = header_map.get("số tiền") or header_map.get("amount") or next((h for h in raw_header if normalize_str(h) == "số tiền"), None)
            person_col = header_map.get("người") or header_map.get("person") or next((h for h in raw_header if normalize_str(h) == "người"), None)
            desc_col = header_map.get("mô tả") or header_map.get("description") or next((h for h in raw_header if normalize_str(h) == "mô tả"), None)
            cat_col = header_map.get("danh mục") or header_map.get("category") or next((h for h in raw_header if normalize_str(h) == "danh mục"), None)

            # Fallback to absolute positions if names fail (ID=0, Date=1, Time=2, Person=3, Cat=4, Amount=5, Desc=6)
            if not date_col and len(raw_header) > 1: date_col = raw_header[1]
            if not amt_col and len(raw_header) > 5: amt_col = raw_header[5]
            if not person_col and len(raw_header) > 3: person_col = raw_header[3]
            if not desc_col and len(raw_header) > 6: desc_col = raw_header[6]
            if not cat_col and len(raw_header) > 4: cat_col = raw_header[4]

            # If essential columns are still not found (very unlikely now), return empty DataFrame
            if not date_col or not amt_col:
                logger.warning("Essential columns (Ngày, Số tiền) not found even with fallback.")
                return pd.DataFrame()

            df = pd.DataFrame(data, columns=raw_header)
            
            # Standardization for date column
            def standardize_date(d):
                if not d or str(d).strip() == "": return pd.NaT # Use NaT for missing/invalid dates
                try:
                    d_str = str(d).strip()
                    # Try to parse with multiple formats
                    dt = pd.to_datetime(d_str, errors='coerce', format='%Y-%m-%d')
                    if pd.isna(dt):
                        dt = pd.to_datetime(d_str, errors='coerce', dayfirst=True)
                    
                    if not pd.isna(dt):
                        return dt.normalize() # Strip time component
                    return pd.NaT
                except:
                    return pd.NaT

            # Apply standardization to create a helper column for matching
            if date_col in df.columns:
                df['__match_date'] = df[date_col].apply(standardize_date)
            else:
                df['__match_date'] = pd.NaT # If date_col not found, all dates are invalid for filtering

            # Filter out rows with invalid dates
            df = df.dropna(subset=['__match_date'])
            
            # Filter logic using ISO string comparison (bulletproof for YYYY-MM-DD)
            if start_date:
                if isinstance(start_date, (date, datetime)):
                    s_dt = pd.Timestamp(start_date.year, start_date.month, start_date.day)
                else:
                    s_dt = pd.to_datetime(start_date, errors='coerce', dayfirst=True)
                if not pd.isna(s_dt):
                    s_dt = s_dt.normalize()
                    df = df[df['__match_date'] >= s_dt]

            if end_date:
                if isinstance(end_date, (date, datetime)):
                    e_dt = pd.Timestamp(end_date.year, end_date.month, end_date.day)
                else:
                    e_dt = pd.to_datetime(end_date, errors='coerce', dayfirst=True)
                if not pd.isna(e_dt):
                    e_dt = e_dt.normalize()
                    df = df[df['__match_date'] <= e_dt]

            if person and person_col and person_col in df.columns:
                df = df[df[person_col].astype(str).str.strip().str.lower() == str(person).strip().lower()]

            # Clean amounts for numeric use
            if amt_col in df.columns:
                df['Số tiền'] = df[amt_col].astype(str).str.replace(r'[^\d]', '', regex=True)
                df['Số tiền'] = pd.to_numeric(df['Số tiền'], errors='coerce').fillna(0).astype(int)
            else:
                df['Số tiền'] = 0 # Default to 0 if amount column is missing or invalid

            # Map important columns to standard names for the bot
            # Ensure these columns exist, even if empty, for consistent output
            df['Mô tả'] = df[desc_col] if desc_col and desc_col in df.columns else ''
            df['Ngày'] = df[date_col] if date_col and date_col in df.columns else ''
            df['Danh mục'] = df[cat_col] if cat_col and cat_col in df.columns else ''
            
            # Drop the temporary match date column
            df = df.drop(columns=['__match_date'])
            
            return df
            
        except Exception as e:
            logger.error(f"FATAL Error in get_expenses: {e}")
            return pd.DataFrame()

    def delete_expense(self, expense_id):
        """Delete an expense by ID."""
        if not self._sheet: self._connect_to_sheets()
        
        try:
            # Find the cell with the ID
            cell = self._sheet.find(str(expense_id))
            if cell:
                self._sheet.delete_rows(cell.row)
                return True
            return False
        except gspread.exceptions.CellNotFound:
            return False
        except Exception as e:
            logger.error(f"Error deleting: {e}")
            return False

    def edit_expense(self, expense_id, new_amount=None, new_description=None):
        """Edit an expense by ID."""
        if not self._sheet: self._connect_to_sheets()
        
        try:
            cell = self._sheet.find(str(expense_id))
            if not cell: return False
            
            row_idx = cell.row
            
            if new_amount is not None:
                # Column 6 is "Số tiền" (F)
                self._sheet.update_cell(row_idx, 6, new_amount)
                
            if new_description is not None:
                # Column 7 is "Mô tả" (G)
                self._sheet.update_cell(row_idx, 7, new_description)
                # Recalculate Category - Column 5 is "Danh mục" (E)
                new_category = classify_expense(new_description)
                self._sheet.update_cell(row_idx, 5, new_category)
                
            return True
        except Exception as e:
            logger.error(f"Error editing: {e}")
            return False

    def get_monthly_summary(self, month=None, year=None, person=None):
        """Get monthly stats using the robust get_expenses logic."""
        now = datetime.now()
        if month is None: month = now.month
        if year is None: year = now.year
        
        # Calculate date range for the month
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(year, month + 1, 1) - timedelta(days=1)
            
        df = self.get_expenses(start_date=start_date, end_date=end_date, person=person)
        
        if df.empty: return None
        
        # We need "Danh mục" column. If missing, use "Other"
        rows = self._sheet.get_all_values()
        header = [str(h).strip().lower() for h in rows[0]]
        cat_col = next((h for i, h in enumerate(rows[0]) if h.strip().lower() == "danh mục"), None)
        
        if cat_col and cat_col in df.columns:
            summary = df.groupby(cat_col)['Số tiền'].sum().to_dict()
        else:
            summary = {"Khác": df['Số tiền'].sum()}
            
        total = sum(summary.values())
        
        return {
            "categories": summary,
            "total": int(total),
            "month": month,
            "year": year,
            "person": person
        }
