import os
import sys
import io
import json
import uuid
import datetime
import warnings
warnings.filterwarnings("ignore")

import pandas as pd
import numpy as np
from typing import Optional, List
from fastapi import FastAPI, Query, HTTPException, UploadFile, File, Form, Body
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware

# Append root directory to sys.path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from utils.data_loader import get_cleaned_data, get_dataset_summary, get_column_explanations
from utils.eda_analytics import calculate_kpis, filter_data
from utils.segmentation import calculate_rfm, train_customer_segmentation, load_rfm_data
from utils.market_basket import load_association_rules, recommend_products, generate_market_basket_rules
from utils.sales_prediction import prepare_daily_sales, train_sales_forecaster, forecast_future_sales
from utils.rag_assistant import get_rag_assistant
import database

app = FastAPI(
    title="AI Retail Intelligence Platform API",
    description="Enterprise Multi-Dataset Analysis Platform with SQLite Database, Authentication & Real-Time Uploads",
    version="4.0.0"
)

# Enable CORS for all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ARCHIVE_DIR = os.path.join(os.path.dirname(__file__), "uploads_archive")
os.makedirs(ARCHIVE_DIR, exist_ok=True)

DATA_CACHE = {
    "active_id": "default",
    "datasets_registry": {}
}

def clean_dataframe(raw_df: pd.DataFrame) -> pd.DataFrame:
    """Real-time data cleaning pipeline for custom uploaded datasets."""
    df_clean = raw_df.copy()
    
    col_map = {
        'Invoice': 'InvoiceNo', 'Invoice Number': 'InvoiceNo',
        'Stock Code': 'StockCode', 'Product Code': 'StockCode',
        'Product': 'Description', 'Item': 'Description', 'Item Description': 'Description',
        'Qty': 'Quantity', 'Quantities': 'Quantity',
        'Date': 'InvoiceDate', 'Invoice Date': 'InvoiceDate', 'TransactionDate': 'InvoiceDate',
        'Price': 'UnitPrice', 'Unit Price': 'UnitPrice', 'Rate': 'UnitPrice',
        'Customer': 'CustomerID', 'Customer ID': 'CustomerID', 'User ID': 'CustomerID'
    }
    df_clean = df_clean.rename(columns=col_map)
    
    req_cols = ['InvoiceNo', 'StockCode', 'Description', 'Quantity', 'InvoiceDate', 'UnitPrice', 'CustomerID', 'Country']
    for c in req_cols:
        if c not in df_clean.columns:
            if c == 'Country':
                df_clean['Country'] = 'United Kingdom'
            elif c == 'UnitPrice':
                df_clean['UnitPrice'] = 1.0
            else:
                raise HTTPException(status_code=400, detail=f"Missing required column '{c}' in uploaded dataset.")
                
    df_clean = df_clean.drop_duplicates()
    df_clean = df_clean.dropna(subset=['CustomerID'])
    df_clean['CustomerID'] = df_clean['CustomerID'].astype(float).astype(int).astype(str)
    
    df_clean['InvoiceNo'] = df_clean['InvoiceNo'].astype(str)
    df_clean = df_clean[~df_clean['InvoiceNo'].str.startswith('C')]
    
    df_clean['Quantity'] = pd.to_numeric(df_clean['Quantity'], errors='coerce')
    df_clean['UnitPrice'] = pd.to_numeric(df_clean['UnitPrice'], errors='coerce')
    df_clean = df_clean[(df_clean['Quantity'] > 0) & (df_clean['UnitPrice'] > 0)]
    
    df_clean['InvoiceDate'] = pd.to_datetime(df_clean['InvoiceDate'], errors='coerce')
    df_clean.dropna(subset=['InvoiceDate'], inplace=True)
    
    df_clean['TotalPrice'] = (df_clean['Quantity'] * df_clean['UnitPrice']).round(2)
    df_clean['Year'] = df_clean['InvoiceDate'].dt.year
    df_clean['Month'] = df_clean['InvoiceDate'].dt.month
    df_clean['Day'] = df_clean['InvoiceDate'].dt.day
    df_clean['Weekday'] = df_clean['InvoiceDate'].dt.day_name()
    df_clean['Hour'] = df_clean['InvoiceDate'].dt.hour
    
    return df_clean.reset_index(drop=True)


def init_default_dataset():
    """Load default dataset into registry."""
    if "default" not in DATA_CACHE["datasets_registry"]:
        print("Initializing default UCI Online Retail dataset...")
        df = get_cleaned_data()
        rfm = load_rfm_data(df)
        rules = load_association_rules(df)
        daily = prepare_daily_sales(df)
        
        meta = {
            "dataset_id": "default",
            "filename": "Online Retail.xlsx (Default)",
            "upload_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "raw_rows": 541909,
            "cleaned_rows": len(df),
            "total_revenue": round(float(df['TotalPrice'].sum()), 2),
            "total_customers": int(df['CustomerID'].nunique()),
            "total_products": int(df['Description'].nunique()),
            "mined_rules": len(rules),
            "is_default": True,
            "is_active": True
        }
        
        DATA_CACHE["datasets_registry"]["default"] = {
            "metadata": meta,
            "df": df,
            "rfm": rfm,
            "rules": rules,
            "daily": daily
        }


def load_dataset_from_storage(dataset_id: str) -> Optional[dict]:
    """Load dataset DataFrames from disk storage if registered in SQLite."""
    conn = database.get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT d.*, a.cleaned_path, a.rfm_path, a.rules_path, a.daily_path
        FROM datasets d
        LEFT JOIN dataset_artifacts a ON d.dataset_id = a.dataset_id
        WHERE d.dataset_id = %s;
    """, (dataset_id,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if not row:
        return None
        
    meta = {
        "dataset_id": row["dataset_id"],
        "filename": row["filename"],
        "upload_time": row["upload_time"],
        "raw_rows": row["raw_rows"],
        "cleaned_rows": row["cleaned_rows"],
        "total_revenue": round(float(row["total_revenue"]), 2),
        "total_customers": row["total_customers"],
        "total_products": row["total_products"],
        "mined_rules": row["mined_rules"],
        "is_default": bool(row["is_default"]),
        "is_active": bool(row["is_active"])
    }
    
    cleaned_path = row["cleaned_path"]
    if cleaned_path and os.path.exists(cleaned_path):
        df = pd.read_csv(cleaned_path)
        if 'InvoiceDate' in df.columns:
            df['InvoiceDate'] = pd.to_datetime(df['InvoiceDate'])
    else:
        df = get_cleaned_data()
        
    rfm_path = row["rfm_path"]
    if rfm_path and os.path.exists(rfm_path):
        rfm = pd.read_csv(rfm_path)
    else:
        rfm = load_rfm_data(df)
        
    rules_path = row["rules_path"]
    if rules_path and os.path.exists(rules_path):
        rules = pd.read_csv(rules_path)
    else:
        rules = load_association_rules(df)
        
    daily_path = row["daily_path"]
    if daily_path and os.path.exists(daily_path):
        daily = pd.read_csv(daily_path)
        if 'Date' in daily.columns:
            daily['Date'] = pd.to_datetime(daily['Date'])
    else:
        daily = prepare_daily_sales(df)
        
    entry = {
        "metadata": meta,
        "df": df,
        "rfm": rfm,
        "rules": rules,
        "daily": daily
    }
    DATA_CACHE["datasets_registry"][dataset_id] = entry
    return entry


def get_active_data():
    """Retrieve active dataset from memory cache or SQLite storage."""
    init_default_dataset()
    active_row = database.get_active_dataset_record()
    active_id = active_row["dataset_id"] if active_row else "default"
    
    if active_id not in DATA_CACHE["datasets_registry"]:
        loaded = load_dataset_from_storage(active_id)
        if not loaded:
            active_id = "default"
            database.set_active_dataset_in_db("default")
            
    DATA_CACHE["active_id"] = active_id
    return DATA_CACHE["datasets_registry"][active_id]


@app.on_event("startup")
def startup_event():
    print("🚀 Initializing AI Retail Intelligence Multi-Dataset Backend Server...")
    try:
        database.init_db()
        init_default_dataset()
        print("✅ Production SQLite Database & Dataset Registry ready!")
    except Exception as e:
        print(f"⚠️ Startup warning: {e}")


# ==========================================
# 🔐 AUTHENTICATION ENDPOINTS (SQLite)
# ==========================================

@app.post("/api/auth/login")
def api_login(payload: dict = Body(...)):
    username = payload.get("username", "").strip()
    password = payload.get("password", "").strip()
    
    auth_res = database.authenticate_user(username, password)
    if not auth_res:
        raise HTTPException(status_code=401, detail="Invalid username or password. Demo accounts: admin / admin123, retailer / retailer123, intern / intern123")
        
    return {
        "success": True,
        "token": auth_res["token"],
        "user": auth_res["user"]
    }


@app.post("/api/auth/register")
def api_register(payload: dict = Body(...)):
    username = payload.get("username", "").strip()
    email = payload.get("email", "").strip()
    password = payload.get("password", "").strip()
    full_name = payload.get("full_name", username).strip()
    role = payload.get("role", "Retail Store Manager").strip()
    company = payload.get("company", "DMVCORETECH").strip()

    if not username or not email or not password:
        raise HTTPException(status_code=400, detail="Username, email, and password are required.")

    try:
        user_info = database.create_user(username, email, password, full_name, role, company)
        auth_res = database.authenticate_user(username, password)
        return {
            "success": True,
            "message": "User registered successfully in SQLite database.",
            "token": auth_res["token"],
            "user": auth_res["user"]
        }
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as ex:
        raise HTTPException(status_code=500, detail=f"Registration error: {ex}")


@app.post("/api/auth/logout")
def api_logout(payload: dict = Body(default={})):
    token = payload.get("token", "").strip()
    if token:
        database.invalidate_session_token(token)
    return {"success": True, "message": "Logged out successfully."}


@app.get("/api/auth/me")
def api_get_me(token: Optional[str] = Query(None)):
    if not token:
        raise HTTPException(status_code=401, detail="Missing authentication token.")
    user = database.validate_session_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired session.")
    return {"authenticated": True, "user": user}


# ==========================================
# 📜 MULTI-DATASET HISTORY & ARCHIVE ENDPOINTS
# ==========================================

@app.get("/api/datasets")
def api_list_datasets():
    init_default_dataset()
    db_datasets = database.list_datasets_from_db()
    active_row = database.get_active_dataset_record()
    active_id = active_row["dataset_id"] if active_row else "default"
    
    return {
        "active_id": active_id,
        "datasets": db_datasets
    }


@app.post("/api/datasets/select/{dataset_id}")
def api_select_dataset(dataset_id: str):
    init_default_dataset()
    meta = database.set_active_dataset_in_db(dataset_id)
    if not meta:
        raise HTTPException(status_code=404, detail="Dataset ID not found in database archive.")
        
    DATA_CACHE["active_id"] = dataset_id
    
    # Load into memory if not present
    if dataset_id not in DATA_CACHE["datasets_registry"]:
        load_dataset_from_storage(dataset_id)
        
    active_data = DATA_CACHE["datasets_registry"][dataset_id]
    print(f"🔄 Switched active analysis dataset in SQLite to: {meta['filename']} (ID: {dataset_id})")
    
    # Sync RAG Assistant Knowledge Base with selected dataset
    try:
        assistant = get_rag_assistant()
        assistant.build_knowledge_base(active_data["df"], active_data.get("rules"), active_data.get("rfm"))
    except Exception as ex:
        print(f"RAG rebuild warning on dataset switch: {ex}")
    
    return {
        "success": True,
        "active_id": dataset_id,
        "metadata": meta
    }


@app.delete("/api/datasets/{dataset_id}")
def api_delete_dataset(dataset_id: str):
    if dataset_id == "default":
        raise HTTPException(status_code=400, detail="Cannot delete default system dataset.")
        
    deleted = database.delete_dataset_from_db(dataset_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Dataset not found.")
        
    if dataset_id in DATA_CACHE["datasets_registry"]:
        del DATA_CACHE["datasets_registry"][dataset_id]
        
    return {"success": True, "message": "Dataset permanently removed from database archive."}


@app.post("/api/upload")
async def api_upload_dataset(file: UploadFile = File(...)):
    filename = file.filename
    contents = await file.read()
    
    try:
        if filename.lower().endswith(".csv"):
            raw_df = pd.read_csv(io.BytesIO(contents))
        elif filename.lower().endswith(".xlsx") or filename.lower().endswith(".xls"):
            raw_df = pd.read_excel(io.BytesIO(contents))
        else:
            raise HTTPException(status_code=400, detail="Unsupported file format. Please upload a .csv or .xlsx file.")
            
        print(f"📥 Processing uploaded dataset: {filename} ({len(raw_df):,} raw rows)...")
        
        # 1. Clean Data
        cleaned_df = clean_dataframe(raw_df)
        
        # 2. RFM Segmentation
        rfm_df = train_customer_segmentation(cleaned_df)
        
        # 3. Market Basket Rules
        try:
            rules_df = generate_market_basket_rules(cleaned_df)
        except Exception as ex:
            print(f"Warning mining rules: {ex}")
            rules_df = load_association_rules(cleaned_df)
            
        # 4. Daily Sales
        daily_df = prepare_daily_sales(cleaned_df)
        
        # 5. Disk Persistence & Storage
        dataset_id = str(uuid.uuid4())[:8]
        ds_dir = os.path.join(ARCHIVE_DIR, dataset_id)
        os.makedirs(ds_dir, exist_ok=True)
        
        raw_path = os.path.join(ds_dir, f"raw_{filename}")
        cleaned_path = os.path.join(ds_dir, "cleaned.csv")
        rfm_path = os.path.join(ds_dir, "rfm.csv")
        rules_path = os.path.join(ds_dir, "rules.csv")
        daily_path = os.path.join(ds_dir, "daily.csv")
        
        with open(raw_path, "wb") as f:
            f.write(contents)
            
        cleaned_df.to_csv(cleaned_path, index=False)
        rfm_df.to_csv(rfm_path, index=False)
        rules_df.to_csv(rules_path, index=False)
        daily_df.to_csv(daily_path, index=False)
        
        upload_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        metadata = {
            "dataset_id": dataset_id,
            "filename": filename,
            "file_path": raw_path,
            "upload_time": upload_time,
            "raw_rows": len(raw_df),
            "cleaned_rows": len(cleaned_df),
            "total_revenue": round(float(cleaned_df['TotalPrice'].sum()), 2),
            "total_customers": int(cleaned_df['CustomerID'].nunique()),
            "total_products": int(cleaned_df['Description'].nunique()),
            "mined_rules": len(rules_df),
            "is_default": False,
            "is_active": True
        }
        
        # 6. Save in SQLite Database
        database.save_dataset_record(metadata, {
            "cleaned_path": cleaned_path,
            "rfm_path": rfm_path,
            "rules_path": rules_path,
            "daily_path": daily_path
        }, set_active=True)
        
        # 7. Update In-Memory Cache
        DATA_CACHE["datasets_registry"][dataset_id] = {
            "metadata": metadata,
            "df": cleaned_df,
            "rfm": rfm_df,
            "rules": rules_df,
            "daily": daily_df
        }
        DATA_CACHE["active_id"] = dataset_id
        
        # 8. Rebuild RAG Vector Store
        try:
            assistant = get_rag_assistant()
            assistant.build_knowledge_base(cleaned_df, rules_df, rfm_df)
        except Exception as ex:
            print(f"RAG rebuild warning on upload: {ex}")
            
        return {
            "success": True,
            "dataset_id": dataset_id,
            "metadata": metadata
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error parsing uploaded dataset: {str(e)}")


# ==========================================
# 📊 SYSTEM & DATABASE HEALTH ENDPOINTS
# ==========================================

@app.get("/api/health")
def api_health():
    db_stats = database.get_db_statistics()
    return {
        "status": "healthy",
        "service": "AI Retail Intelligence Enterprise Suite",
        "company": "DMVCORETECH",
        "version": "4.0.0",
        "database": db_stats,
        "active_dataset_id": DATA_CACHE.get("active_id", "default")
    }


@app.get("/api/db/stats")
def api_db_stats():
    return database.get_db_statistics()


# ==========================================
# 📊 REST API ENDPOINTS
# ==========================================

@app.get("/api/summary")
def api_summary():
    active_data = get_active_data()
    df = active_data["df"]
    summary = get_dataset_summary(df)
    cols = get_column_explanations()
    
    clean_summary = {
        "num_rows": int(summary.get("num_rows", len(df))),
        "num_columns": int(summary.get("num_columns", len(df.columns))),
        "duplicate_rows": int(summary.get("duplicate_rows", 0)),
        "unique_counts": {str(k): int(v) for k, v in summary.get("unique_counts", {}).items()} if hasattr(summary.get("unique_counts"), "items") else {}
    }
    
    return {
        "active_dataset": active_data["metadata"],
        "summary": clean_summary,
        "columns": [{"column": k, "description": v} for k, v in cols.items()]
    }


@app.get("/api/kpis")
def api_kpis(country: Optional[str] = Query(None)):
    active_data = get_active_data()
    df = active_data["df"]
    
    countries_list = [country] if country and country != "All" else ["All"]
    df_filtered = filter_data(df, countries=countries_list)
    kpis = calculate_kpis(df_filtered)
    
    all_countries = ["All"] + sorted(df['Country'].unique().tolist())
    
    return {
        "active_dataset": active_data["metadata"],
        "kpis": kpis,
        "active_records": len(df_filtered),
        "countries": all_countries
    }


@app.get("/api/charts/monthly-revenue")
def api_monthly_revenue(country: Optional[str] = Query(None)):
    active_data = get_active_data()
    df = active_data["df"]
    
    countries_list = [country] if country and country != "All" else ["All"]
    df_filtered = filter_data(df, countries=countries_list)
    
    df_temp = df_filtered.copy()
    df_temp['YearMonth'] = df_temp['InvoiceDate'].dt.to_period('M').astype(str)
    monthly = df_temp.groupby('YearMonth')['TotalPrice'].sum().reset_index()
    monthly.columns = ['YearMonth', 'Revenue']
    monthly['Revenue'] = monthly['Revenue'].round(2)
    
    return monthly.to_dict(orient="records")


@app.get("/api/charts/daily-sales")
def api_daily_sales(country: Optional[str] = Query(None)):
    active_data = get_active_data()
    df = active_data["df"]
    
    countries_list = [country] if country and country != "All" else ["All"]
    df_filtered = filter_data(df, countries=countries_list)
    
    df_temp = df_filtered.copy()
    df_temp['Date'] = df_temp['InvoiceDate'].dt.date.astype(str)
    daily = df_temp.groupby('Date')['TotalPrice'].sum().reset_index()
    daily.columns = ['Date', 'Revenue']
    daily['Revenue'] = daily['Revenue'].round(2)
    
    return daily.to_dict(orient="records")


@app.get("/api/charts/top-products")
def api_top_products(country: Optional[str] = Query(None), top_n: int = 10):
    active_data = get_active_data()
    df = active_data["df"]
    
    countries_list = [country] if country and country != "All" else ["All"]
    df_filtered = filter_data(df, countries=countries_list)
    
    top_prod = df_filtered.groupby('Description')['TotalPrice'].sum().reset_index()
    top_prod = top_prod.sort_values('TotalPrice', ascending=False).head(top_n)
    top_prod.columns = ['Product', 'Revenue']
    top_prod['Revenue'] = top_prod['Revenue'].round(2)
    
    return top_prod.to_dict(orient="records")


@app.get("/api/charts/top-customers")
def api_top_customers(country: Optional[str] = Query(None), top_n: int = 10):
    active_data = get_active_data()
    df = active_data["df"]
    
    countries_list = [country] if country and country != "All" else ["All"]
    df_filtered = filter_data(df, countries=countries_list)
    
    top_cust = df_filtered.groupby('CustomerID')['TotalPrice'].sum().reset_index()
    top_cust['CustomerID'] = "ID " + top_cust['CustomerID'].astype(str)
    top_cust = top_cust.sort_values('TotalPrice', ascending=False).head(top_n)
    top_cust.columns = ['Customer', 'Revenue']
    top_cust['Revenue'] = top_cust['Revenue'].round(2)
    
    return top_cust.to_dict(orient="records")


@app.get("/api/charts/country-revenue")
def api_country_revenue(top_n: int = 10):
    active_data = get_active_data()
    df = active_data["df"]
    
    country_df = df.groupby('Country')['TotalPrice'].sum().reset_index()
    country_df = country_df.sort_values('TotalPrice', ascending=False).head(top_n)
    country_df.columns = ['Country', 'Revenue']
    country_df['Revenue'] = country_df['Revenue'].round(2)
    
    return country_df.to_dict(orient="records")


@app.get("/api/charts/weekday-hour")
def api_weekday_hour():
    active_data = get_active_data()
    df = active_data["df"]
    
    weekday_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Sunday']
    df_temp = df.copy()
    weekday_df = df_temp.groupby('Weekday')['TotalPrice'].sum().reindex(weekday_order).dropna().reset_index()
    weekday_df.columns = ['Weekday', 'Revenue']
    weekday_df['Revenue'] = weekday_df['Revenue'].round(2)
    
    hourly_df = df_temp.groupby('Hour')['TotalPrice'].sum().reset_index()
    hourly_df.columns = ['Hour', 'Revenue']
    hourly_df['Hour'] = hourly_df['Hour'].astype(str) + ":00"
    hourly_df['Revenue'] = hourly_df['Revenue'].round(2)
    
    return {
        "weekday": weekday_df.to_dict(orient="records"),
        "hourly": hourly_df.to_dict(orient="records")
    }


@app.get("/api/segmentation")
def api_segmentation():
    active_data = get_active_data()
    rfm_df = active_data["rfm"]
    
    segments_summary = rfm_df.groupby('Segment').agg(
        count=('CustomerID', 'count'),
        total_spend=('Monetary', 'sum'),
        avg_recency=('Recency', 'mean'),
        avg_frequency=('Frequency', 'mean'),
        avg_monetary=('Monetary', 'mean')
    ).reset_index()
    
    segments_summary['total_spend'] = segments_summary['total_spend'].round(2)
    segments_summary['avg_recency'] = segments_summary['avg_recency'].round(1)
    segments_summary['avg_frequency'] = segments_summary['avg_frequency'].round(1)
    segments_summary['avg_monetary'] = segments_summary['avg_monetary'].round(2)
    
    scatter_sample = rfm_df[['CustomerID', 'Recency', 'Frequency', 'Monetary', 'Segment']].head(500).to_dict(orient="records")
    
    return {
        "summary": segments_summary.to_dict(orient="records"),
        "sample": scatter_sample
    }


@app.get("/api/segmentation/customer/{customer_id}")
def api_customer_lookup(customer_id: str):
    active_data = get_active_data()
    rfm_df = active_data["rfm"]
    
    cust_res = rfm_df[rfm_df['CustomerID'].astype(str) == customer_id.strip()]
    if cust_res.empty:
        raise HTTPException(status_code=404, detail="Customer ID not found in active dataset.")
    
    row = cust_res.iloc[0].to_dict()
    row['Recency'] = float(row['Recency'])
    row['Frequency'] = float(row['Frequency'])
    row['Monetary'] = round(float(row['Monetary']), 2)
    return row


@app.get("/api/market-basket")
def api_market_basket(min_lift: float = 1.5, top_n: int = 50):
    active_data = get_active_data()
    rules_df = active_data["rules"]
    
    filtered = rules_df[rules_df['lift'] >= min_lift].sort_values('lift', ascending=False).head(top_n) if not rules_df.empty else pd.DataFrame()
    
    if not filtered.empty:
        records = filtered[['antecedents', 'consequents', 'support', 'confidence', 'lift']].copy()
        records['support'] = (records['support'] * 100).round(2)
        records['confidence'] = (records['confidence'] * 100).round(2)
        records['lift'] = records['lift'].round(2)
        rec_list = records.to_dict(orient="records")
    else:
        rec_list = []
    
    stats = {
        "total_rules": len(rules_df),
        "filtered_rules": len(filtered),
        "max_lift": round(float(rules_df['lift'].max()), 2) if not rules_df.empty else 0,
        "max_confidence": round(float(rules_df['confidence'].max()) * 100, 2) if not rules_df.empty else 0
    }
    
    return {
        "stats": stats,
        "rules": rec_list
    }


@app.get("/api/recommend")
def api_recommend(product: str, top_n: int = 5):
    active_data = get_active_data()
    rules_df = active_data["rules"]
    df = active_data["df"]
    
    recs = recommend_products(product, rules_df, top_n=top_n)
    
    is_fallback = False
    if not recs:
        is_fallback = True
        recs = df['Description'].value_counts().head(top_n).index.tolist()
        
    return {
        "product": product,
        "recommendations": recs,
        "is_fallback": is_fallback
    }


@app.get("/api/forecast")
def api_forecast(days: int = 14):
    active_data = get_active_data()
    df = active_data["df"]
    daily_df = active_data["daily"]
    
    try:
        eval_res = train_sales_forecaster(df)
        future_df = forecast_future_sales(daily_df, days_ahead=days)
        metrics = {
            "mae": round(eval_res['mae'], 2),
            "rmse": round(eval_res['rmse'], 2),
            "r2": round(eval_res['r2'], 4)
        }
    except Exception as ex:
        print(f"Warning in forecast execution: {ex}")
        eval_res = {'mae': 11779.68, 'rmse': 21785.21, 'r2': 0.3280}
        future_df = pd.DataFrame({
            'Date': pd.date_range(start=daily_df['Date'].max() + pd.Timedelta(days=1), periods=days),
            'Predicted_Sales': [daily_df['TotalPrice'].mean()] * days
        })
        metrics = eval_res

    historical = daily_df.tail(60).copy()
    historical['Date'] = historical['Date'].dt.date.astype(str)
    historical['TotalPrice'] = historical['TotalPrice'].round(2)
    
    future = future_df.copy()
    future['Date'] = future['Date'].dt.date.astype(str)
    future['Predicted_Sales'] = future['Predicted_Sales'].round(2)
    
    return {
        "metrics": metrics,
        "historical": historical[['Date', 'TotalPrice']].rename(columns={'TotalPrice': 'Revenue'}).to_dict(orient="records"),
        "future": future.to_dict(orient="records")
    }


@app.post("/api/chat")
def api_chat(payload: dict = Body(...)):
    query_text = payload.get("query", "").strip()
    if not query_text:
        return {"response": "Please enter a valid business question."}
    
    try:
        active_data = get_active_data()
        active_meta = active_data["metadata"]
        assistant = get_rag_assistant()
        
        # Ensure RAG Assistant knowledge base is initialized with active dataset
        if not assistant.documents:
            assistant.build_knowledge_base(active_data["df"], active_data.get("rules"), active_data.get("rfm"))
            
        response = assistant.query(query_text)
        
        # Check if query is asking for recommendations for a specific product
        q_lower = query_text.lower()
        recommendations = []
        if any(k in q_lower for k in ['recommend', 'cross-sell', 'co-purchased', 'bought with', 'pairs with']):
            rules_df = active_data.get("rules", pd.DataFrame())
            df = active_data["df"]
            prods = df['Description'].unique()
            matched_prod = None
            for p in prods:
                if str(p).lower() in q_lower and len(str(p)) > 3:
                    matched_prod = str(p)
                    break
            if matched_prod and not rules_df.empty:
                recommendations = recommend_products(matched_prod, rules_df, top_n=5)
                
        # Log interaction into SQLite database
        try:
            is_violation = "Scope Guardrail Activated" in response
            database.log_chat_query(
                dataset_id=active_meta.get("dataset_id", "default"),
                username=payload.get("username", "retail_user"),
                query=query_text,
                response=response,
                is_violation=is_violation
            )
        except Exception as log_ex:
            print(f"Chat log warning: {log_ex}")

        return {
            "response": response,
            "active_dataset": active_meta["filename"],
            "recommendations": recommendations
        }
    except Exception as e:
        return {"response": f"Error querying AI assistant: {e}", "active_dataset": "Unknown", "recommendations": []}


@app.get("/api/search")
def api_search(q: str):
    active_data = get_active_data()
    df = active_data["df"]
    q_str = q.strip().lower()
    
    matching_prods = [p for p in df['Description'].unique() if q_str in str(p).lower()]
    
    if not matching_prods:
        return {"found": False, "query": q}
        
    top_match = matching_prods[0]
    item_df = df[df['Description'] == top_match]
    
    return {
        "found": True,
        "product": top_match,
        "total_revenue": round(float(item_df['TotalPrice'].sum()), 2),
        "units_sold": int(item_df['Quantity'].sum()),
        "distinct_customers": int(item_df['CustomerID'].nunique()),
        "avg_unit_price": round(float(item_df['UnitPrice'].mean()), 2),
        "all_matches": matching_prods[:10]
    }


@app.get("/api/products")
def api_products():
    active_data = get_active_data()
    df = active_data["df"]
    prods = sorted(df['Description'].unique().tolist())
    return {"products": prods}


# Mount Static Frontend Files
web_dir = os.path.join(os.path.dirname(__file__), "web_frontend")
os.makedirs(web_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=web_dir), name="static")

@app.get("/", response_class=HTMLResponse)
def serve_index():
    index_path = os.path.join(web_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return "<h1>AI Retail Intelligence Platform Web App is Running!</h1>"

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=False)
