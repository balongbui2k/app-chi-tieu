import pandas as pd
import os
from datetime import datetime
import config
from categories import classify_expense

class ExpenseManager:
    def __init__(self):
        self.data_dir = config.DATA_DIR
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)

    def _get_file_path(self, date=None):
        """Generate file path based on year and month."""
        if date is None:
            date = datetime.now()
        year_dir = os.path.join(self.data_dir, date.strftime("%Y"))
        if not os.path.exists(year_dir):
            os.makedirs(year_dir)
        filename = date.strftime("%B.xlsx")
        return os.path.join(year_dir, filename)

    def add_expense(self, amount, description, person="Bản thân", date=None):
        """Add a new expense record."""
        if date is None:
            date = datetime.now()
        
        category = classify_expense(description)
        file_path = self._get_file_path(date)
        
        new_row = {
            "ID": int(datetime.timestamp(datetime.now()) * 1000), # Unique ID
            "Ngày": date.strftime("%d/%m/%Y"),
            "Giờ": date.strftime("%H:%M:%S"),
            "Người": person,
            "Danh mục": category,
            "Số tiền": amount,
            "Mô tả": description
        }
        
        if os.path.exists(file_path):
            df = pd.read_excel(file_path)
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        else:
            df = pd.DataFrame([new_row])
            
        df.to_excel(file_path, index=False)
        return new_row

    def get_expenses(self, start_date=None, end_date=None, person=None):
        """Retrieve expenses for a given period and optionally filter by person."""
        # Simple implementation for now: current month
        file_path = self._get_file_path()
        if not os.path.exists(file_path):
            return pd.DataFrame()
        
        df = pd.read_excel(file_path)
        # Filter by date if provided (need to convert 'Ngày' column to datetime)
        df['Ngày_dt'] = pd.to_datetime(df['Ngày'], format='%d/%m/%Y')
        
        if start_date and end_date:
            mask = (df['Ngày_dt'] >= start_date) & (df['Ngày_dt'] <= end_date)
            df = df.loc[mask]
        
        if person:
            df = df[df['Người'] == person]
        
        return df

    def delete_expense(self, expense_id):
        """Delete an expense record by ID."""
        file_path = self._get_file_path()
        if not os.path.exists(file_path):
            return False
            
        df = pd.read_excel(file_path)
        if expense_id in df['ID'].values:
            df = df[df['ID'] != expense_id]
            df.to_excel(file_path, index=False)
            return True
        return False

    def edit_expense(self, expense_id, new_amount=None, new_description=None):
        """Edit an existing expense record."""
        file_path = self._get_file_path()
        if not os.path.exists(file_path):
            return False
            
        df = pd.read_excel(file_path)
        if expense_id in df['ID'].values:
            idx = df[df['ID'] == expense_id].index[0]
            if new_amount is not None:
                df.at[idx, 'Số tiền'] = new_amount
            if new_description is not None:
                df.at[idx, 'Mô tả'] = new_description
                df.at[idx, 'Danh mục'] = classify_expense(new_description)
            
            df.to_excel(file_path, index=False)
            return True
        return False

    def get_monthly_summary(self, month=None, year=None, person=None):
        """Get summary statistics for a specific month, optionally filtered by person."""
        now = datetime.now()
        if month is None: month = now.month
        if year is None: year = now.year
        
        date = datetime(year, month, 1)
        file_path = self._get_file_path(date)
        
        if not os.path.exists(file_path):
            return None
            
        df = pd.read_excel(file_path)
        
        if person:
            df = df[df['Người'] == person]
        
        summary = df.groupby('Danh mục')['Số tiền'].sum().to_dict()
        total = sum(summary.values())
        
        return {
            "categories": summary,
            "total": total,
            "month": month,
            "year": year,
            "person": person
        }
