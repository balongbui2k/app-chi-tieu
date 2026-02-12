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
        """Retrieve expenses with extreme robustness (String-based comparison)."""
        if not self._sheet: self._connect_to_sheets()
        
        required_cols = ["ID", "Ngày", "Giờ", "Người", "Danh mục", "Số tiền", "Mô tả", "Tháng", "Năm"]
        
        try:
            # Using get_all_values() is more robust for manual header detection
            rows = self._sheet.get_all_values()
            if len(rows) <= 1:
                return pd.DataFrame(columns=required_cols)
            
            # Use the first row as headers, and data from 2nd row
            header = rows[0]
            data = rows[1:]
            df = pd.DataFrame(data, columns=header)
            
            # Ensure all required columns exist and are strings initially
            for col in required_cols:
                if col not in df.columns:
                    df[col] = ""
                else:
                    df[col] = df[col].astype(str)

            if df.empty:
                return df

            # Clean 'Số tiền'
            df['Số tiền_clean'] = df['Số tiền'].str.replace(r'[^\d]', '', regex=True)
            df['Số tiền_num'] = pd.to_numeric(df['Số tiền_clean'], errors='coerce').fillna(0).astype(int)

            # --- ULTIMATE STRING-BASED FILTERING ---
            # Standardize comparison: Always use YYYY-MM-DD strings
            if start_date:
                if isinstance(start_date, (datetime, date)):
                    start_str = start_date.strftime("%Y-%m-%d")
                else:
                    start_str = str(start_date)[:10] 
                df = df[df['Ngày'].astype(str) >= start_str]
                
            if end_date:
                if isinstance(end_date, (datetime, date)):
                    end_str = end_date.strftime("%Y-%m-%d")
                else:
                    end_str = str(end_date)[:10]
                df = df[df['Ngày'].astype(str) <= end_str]
            
            if person:
                df = df[df['Người'].astype(str).str.strip() == str(person).strip()]
            
            # Map back for the bot to use 'Số tiền' as the numeric one
            df['Số tiền'] = df['Số tiền_num']
            return df
            
        except Exception as e:
            logger.error(f"FATAL Error fetching data: {e}")
            return pd.DataFrame(columns=required_cols)

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
