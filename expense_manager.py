import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from datetime import datetime, date
import config
from categories import classify_expense
import logging

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
            try:
                self._sheet = self._client.open(config.GOOGLE_SHEET_NAME).sheet1
            except gspread.exceptions.SpreadsheetNotFound:
                # If "Sheet1" or file not found, try creating it? 
                # Better to just instruct user, but we can try to find first sheet
                try:
                    self._sheet = self._client.open(config.GOOGLE_SHEET_NAME).get_worksheet(0)
                except Exception as e:
                    logger.error(f"Could not open sheet '{config.GOOGLE_SHEET_NAME}': {e}")
                    raise

            # Initialize headers if empty
            if not self._sheet.get_all_values():
                self._sheet.append_row(["ID", "Ngày", "Giờ", "Người", "Danh mục", "Số tiền", "Mô tả", "Tháng", "Năm"])
                
        except Exception as e:
            logger.error(f"Google Sheets Connection Error: {e}")

    def add_expense(self, amount, description, person="Bản thân", date=None):
        """Add a new expense record to Google Sheets."""
        if not self._sheet: self._connect_to_sheets()
        
        if date is None:
            date = datetime.now()
        
        category = classify_expense(description)
        
        # Format timestamps correctly (Using ISO format YYYY-MM-DD is bulletproof)
        day_str = date.strftime("%Y-%m-%d")
        time_str = date.strftime("%H:%M:%S")
        month = date.month
        year = date.year
        expense_id = int(datetime.timestamp(datetime.now()) * 1000)

        # Row data
        row = [
            str(expense_id), day_str, time_str, person, category, amount, description, month, year
        ]
        
        try:
            self._sheet.append_row(row)
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
        """Retrieve expenses with dynamic column detection and extreme robustness."""
        if not self._sheet: self._connect_to_sheets()
        
        try:
            rows = self._sheet.get_all_values()
            if len(rows) <= 1:
                return pd.DataFrame()
            
            # Normalize headers
            raw_header = [str(h).strip() for h in rows[0]]
            data = rows[1:]
            
            # Find index of "Ngày" column (case-insensitive)
            col_map = {h.lower(): i for i, h in enumerate(raw_header)}
            date_col = next((h for h in raw_header if h.lower() == "ngày"), "Ngày")
            amt_col = next((h for h in raw_header if h.lower() == "số tiền"), "Số tiền")
            person_col = next((h for h in raw_header if h.lower() == "người"), "Người")
            desc_col = next((h for h in raw_header if h.lower() == "mô tả"), "Mô tả")

            df = pd.DataFrame(data, columns=raw_header)
            
            # Standardization
            if date_col in df.columns:
                def standardize(d):
                    if not d: return "0000-00-00"
                    try:
                        # Try parsing various formats
                        dt = pd.to_datetime(d, dayfirst=True, errors='coerce')
                        if pd.isna(dt): return str(d) # Keep as is if failed
                        return dt.strftime("%Y-%m-%d")
                    except:
                        return str(d)
                df['__match_date'] = df[date_col].apply(standardize)
            else:
                df['__match_date'] = "0000-00-00"

            # Filter logic
            if start_date:
                s_str = start_date.strftime("%Y-%m-%d") if isinstance(start_date, (date, datetime)) else str(start_date)[:10]
                df = df[df['__match_date'] >= s_str]
            if end_date:
                e_str = end_date.strftime("%Y-%m-%d") if isinstance(end_date, (date, datetime)) else str(end_date)[:10]
                df = df[df['__match_date'] <= e_str]

            if person and person_col in df.columns:
                df = df[df[person_col].astype(str).str.strip().str.lower() == str(person).strip().lower()]

            # Clean amounts for numeric use
            if amt_col in df.columns:
                df['Số tiền'] = df[amt_col].astype(str).str.replace(r'[^\d]', '', regex=True)
                df['Số tiền'] = pd.to_numeric(df['Số tiền'], errors='coerce').fillna(0).astype(int)
            else:
                df['Số tiền'] = 0

            # Map important columns to standard names for the bot
            if desc_col in df.columns: df['Mô tả'] = df[desc_col]
            if date_col in df.columns: df['Ngày'] = df[date_col]
            
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
