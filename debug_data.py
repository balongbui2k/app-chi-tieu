from expense_manager import ExpenseManager
import pandas as pd

em = ExpenseManager()
rows = em._sheet.get_all_values()
print(f"Total rows: {len(rows)}")
if rows:
    print(f"Headers: {rows[0]}")
    for i, row in enumerate(rows[1:10]):
        print(f"Row {i+1}: {row}")

df = em.get_expenses()
print("\nDataFrame Info:")
print(df.info())
print("\nDataFrame Head:")
print(df.head())

# Test today's filter
from datetime import datetime
import pytz
vn_tz = pytz.timezone('Asia/Ho_Chi_Minh')
now = datetime.now(vn_tz)
today_str = now.strftime("%Y-%m-%d")
print(f"\nFiltering for today: {today_str}")
df_today = em.get_expenses(start_date=today_str, end_date=today_str)
print(f"Today total rows: {len(df_today)}")
if not df_today.empty:
    print(df_today)
else:
    print("Today is empty!")
