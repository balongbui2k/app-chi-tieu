import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from datetime import datetime
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
        
        # Format timestamps
        day_str = date.strftime("%d/%m/%Y")
        time_str = date.strftime("%H:%M:%S")
        month = date.month
        year = date.year
        expense_id = int(datetime.timestamp(datetime.now()) * 1000)

        # Row data
        row = [
            expense_id, day_str, time_str, person, category, amount, description, month, year
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
        """Retrieve expenses as a DataFrame."""
        if not self._sheet: self._connect_to_sheets()
        
        try:
            data = self._sheet.get_all_records()
            if not data:
                return pd.DataFrame()
                
            df = pd.DataFrame(data)
            
            # Ensure columns exist even if empty
            required_cols = ["ID", "Ngày", "Giờ", "Người", "Danh mục", "Số tiền", "Mô tả"]
            for col in required_cols:
                if col not in df.columns:
                    return pd.DataFrame() # Malformed sheet

            # Convert types
            df['Số tiền'] = pd.to_numeric(df['Số tiền'], errors='coerce').fillna(0).astype(int)
            df['Ngày_dt'] = pd.to_datetime(df['Ngày'], format='%d/%m/%Y', errors='coerce')

            # Filter
            if start_date:
                df = df[df['Ngày_dt'] >= start_date]
            if end_date:
                df = df[df['Ngày_dt'] <= end_date]
            if person:
                df = df[df['Người'] == person]
                
            return df
            
        except Exception as e:
            logger.error(f"Error fetching data: {e}")
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
        """Get monthly stats."""
        if not self._sheet: self._connect_to_sheets()
        
        now = datetime.now()
        if month is None: month = now.month
        if year is None: year = now.year
        
        try:
            data = self._sheet.get_all_records()
            if not data: return None
            
            df = pd.DataFrame(data)
            
            # Simple conversion for filtering
            df['Tháng'] = pd.to_numeric(df['Tháng'], errors='coerce')
            df['Năm'] = pd.to_numeric(df['Năm'], errors='coerce')
            df['Số tiền'] = pd.to_numeric(df['Số tiền'], errors='coerce').fillna(0)
            
            # Filter
            mask = (df['Tháng'] == month) & (df['Năm'] == year)
            if person:
                mask = mask & (df['Người'] == person)
                
            filtered = df[mask]
            
            if filtered.empty: return None
            
            summary = filtered.groupby('Danh mục')['Số tiền'].sum().to_dict()
            total = sum(summary.values())
            
            return {
                "categories": summary,
                "total": int(total),
                "month": month,
                "year": year,
                "person": person
            }
        except Exception as e:
            logger.error(f"Error summarizing: {e}")
            return None
