import pandas as pd
d = '2026-02-13'
dt = pd.to_datetime(d, dayfirst=True, errors='coerce')
print(f"dt: {dt}")
print(f"formatted: {dt.strftime('%Y-%m-%d') if not pd.isna(dt) else 'NaT'}")

d2 = '13/02/2026'
dt2 = pd.to_datetime(d2, dayfirst=True, errors='coerce')
print(f"dt2: {dt2}")
print(f"formatted2: {dt2.strftime('%Y-%m-%d') if not pd.isna(dt) else 'NaT'}")
