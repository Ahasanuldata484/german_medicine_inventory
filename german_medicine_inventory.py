import re
import pandas as pd
from sqlalchemy import create_engine, text, types

# 1. Loading Excel file (absolute path)
excel_path = r"C:\Users\Go to your Excel file\Right click on it\Copy as path\and paste it here\data_engineering\german_medicine_inventory_all\german_medicine_inventory.xlsx"
df = pd.read_excel(excel_path)

# 2. PostgreSQL Connection
db_user = 'postgres'
db_password = 'Your Password'   # replace with your actual password
db_host = 'localhost'
db_port = '5432'
db_name = 'postgres'

engine = create_engine(f'postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}')

# 3. Schema creation
with engine.connect() as conn:
    conn.execute(text("CREATE SCHEMA IF NOT EXISTS sales_business;"))
    conn.commit()

# 4. Cleaning Column names
df.columns = [
    re.sub(r'[^a-z0-9_]', '', str(col).strip().lower().replace(" ", "_").replace("()", "-").replace(".", "_")) 
    for col in df.columns
]

# 5. Cleaning Rows
def clean_row_data(value):
    if not isinstance(value, str):
        return value
    
    cleaned = value.lower()
    cleaned = cleaned.replace('/', '-')
    cleaned = re.sub(r'[^a-z0-9\s\-\.\:\*]', '', cleaned)
    cleaned = re.sub(r'\s+', '_', cleaned)
    cleaned = cleaned.strip('_')
    
    return cleaned

for col in df.columns:
    # Will clean only text columns, this won't work on numeric columns
    if col not in ['wholesale_price', 'retail_price', 'qt_only_number']:
        df[col] = df[col].map(clean_row_data)

# Extra safety: If there is any text or dirty data in the numeric columns, clean it and convert it to float
df['wholesale_price'] = pd.to_numeric(df['wholesale_price'].astype(str).str.replace(r'[^0-9.]', '', regex=True), errors='coerce')
df['retail_price'] = pd.to_numeric(df['retail_price'].astype(str).str.replace(r'[^0-9.]', '', regex=True), errors='coerce')
df['qt_only_number'] = pd.to_numeric(df['qt_only_number'], errors='coerce').fillna(0).astype(int)
df['expiry_date'] = pd.to_datetime(df['expiry_date'], errors='coerce')

# 6. Loading data into the database
try:
    df.to_sql(
        name='german_medicine_inventory',
        con=engine,
        schema='sales_business',
        if_exists='replace',
        index=False,
        method='multi',
        
        dtype={
            'medicine_generic_name': types.VARCHAR(80),
            'quantity': types.VARCHAR(30),
            'wholesale_price': types.Numeric(10, 2),
            'retail_price': types.Numeric(10, 2),
            'qt_only_number': types.SmallInteger(),
            'expiry_date': types.Date()
        }
    )
    print("Data moved from Excel to PostgreSQL successfully!")
except Exception as e:
    print(f"An error occurred: {e}")
