import os
import pandas as pd
import numpy as np

RAW_DATA_PATH = os.path.join("data", "raw", "Online Retail.xlsx")
PROCESSED_DATA_PATH = os.path.join("data", "processed", "cleaned_retail_data.csv")

COLUMN_EXPLANATIONS = {
    "InvoiceNo": "A 6-digit integral number uniquely assigned to each transaction. If starting with 'C', indicates a cancellation.",
    "StockCode": "Product (item) code. A 5-digit integral number uniquely assigned to each distinct product.",
    "Description": "Product (item) name / description.",
    "Quantity": "The quantities of each product (item) per transaction.",
    "InvoiceDate": "Invoice Date and time when each transaction was generated.",
    "UnitPrice": "Unit price of product in Sterling (£) per unit.",
    "CustomerID": "Customer number. A 5-digit integral number uniquely assigned to each customer.",
    "Country": "Country name where customer resides.",
    "TotalPrice": "Total transaction amount for the line item (Quantity × UnitPrice).",
    "Year": "Year extracted from InvoiceDate.",
    "Month": "Month extracted from InvoiceDate.",
    "Day": "Day of the month extracted from InvoiceDate.",
    "Weekday": "Day of the week (Monday=0 ... Sunday=6).",
    "Hour": "Hour of the day (0 to 23) when invoice was generated."
}


def get_column_explanations():
    """Return dictionary explaining each column."""
    return COLUMN_EXPLANATIONS


def load_raw_data(filepath: str = RAW_DATA_PATH) -> pd.DataFrame:
    """Load raw dataset from Excel file."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Raw data file not found at: {filepath}")
    df = pd.read_excel(filepath)
    return df


def get_dataset_summary(df: pd.DataFrame) -> dict:
    """Calculate and return Module 1 understanding metrics."""
    # Handle missing CustomerID safely for counting
    cust_series = df['CustomerID'].dropna() if 'CustomerID' in df.columns else pd.Series()
    
    summary = {
        "shape": df.shape,
        "num_rows": df.shape[0],
        "num_columns": df.shape[1],
        "columns": list(df.columns),
        "data_types": df.dtypes.astype(str).to_dict(),
        "missing_values": df.isnull().sum().to_dict(),
        "duplicate_rows": int(df.duplicated().sum()),
        "unique_customers": int(cust_series.nunique()),
        "unique_products": int(df['StockCode'].nunique()) if 'StockCode' in df.columns else 0,
        "unique_countries": int(df['Country'].nunique()) if 'Country' in df.columns else 0,
        "unique_invoices": int(df['InvoiceNo'].nunique()) if 'InvoiceNo' in df.columns else 0,
        "statistical_summary": df.describe(include='all').astype(str).to_dict()
    }
    return summary


def clean_data(raw_filepath: str = RAW_DATA_PATH, save_processed: bool = True) -> pd.DataFrame:
    """
    Perform Module 2 Data Cleaning:
    - Remove duplicate rows
    - Remove cancelled invoices (InvoiceNo starts with 'C')
    - Remove rows having Quantity <= 0
    - Remove rows having UnitPrice <= 0
    - Remove rows where CustomerID is missing
    - Convert InvoiceDate to datetime format
    - Create TotalPrice = Quantity * UnitPrice
    - Extract Year, Month, Day, Weekday, Hour
    - Save cleaned dataset to data/processed/cleaned_retail_data.csv
    """
    df = load_raw_data(raw_filepath)
    
    # 1. Remove duplicate rows
    df = df.drop_duplicates()
    
    # 2. Remove missing CustomerID
    df = df.dropna(subset=['CustomerID'])
    df['CustomerID'] = df['CustomerID'].astype(int).astype(str)
    
    # 3. Remove cancelled invoices (InvoiceNo starting with 'C')
    df['InvoiceNo'] = df['InvoiceNo'].astype(str)
    df = df[~df['InvoiceNo'].str.upper().str.startswith('C')]
    
    # 4. Remove Quantity <= 0 & UnitPrice <= 0
    df = df[df['Quantity'] > 0]
    df = df[df['UnitPrice'] > 0]
    
    # 5. Clean Description string
    if 'Description' in df.columns:
        df['Description'] = df['Description'].astype(str).str.strip().str.upper()
    
    # 6. Convert InvoiceDate into datetime format
    df['InvoiceDate'] = pd.to_datetime(df['InvoiceDate'])
    
    # 7. Create TotalPrice
    df['TotalPrice'] = df['Quantity'] * df['UnitPrice']
    
    # 8. Extract Date Features
    df['Year'] = df['InvoiceDate'].dt.year
    df['Month'] = df['InvoiceDate'].dt.month
    df['Day'] = df['InvoiceDate'].dt.day
    df['Weekday'] = df['InvoiceDate'].dt.day_name()
    df['WeekdayNum'] = df['InvoiceDate'].dt.weekday
    df['Hour'] = df['InvoiceDate'].dt.hour
    
    if save_processed:
        os.makedirs(os.path.dirname(PROCESSED_DATA_PATH), exist_ok=True)
        df.to_csv(PROCESSED_DATA_PATH, index=False)
        print(f"Cleaned dataset saved successfully to: {PROCESSED_DATA_PATH}")
        
    return df


def get_cleaned_data(filepath: str = PROCESSED_DATA_PATH, force_reclean: bool = False) -> pd.DataFrame:
    """Load cached cleaned data or run clean_data() if file missing."""
    if force_reclean or not os.path.exists(filepath):
        return clean_data(save_processed=True)
    df = pd.read_csv(filepath)
    df['InvoiceDate'] = pd.to_datetime(df['InvoiceDate'])
    df['CustomerID'] = df['CustomerID'].astype(str)
    return df


if __name__ == "__main__":
    print("Testing Data Loader & Cleaning Module...")
    cleaned_df = clean_data()
    print("Cleaned DataFrame Shape:", cleaned_df.shape)
    print(cleaned_df.head(3))
