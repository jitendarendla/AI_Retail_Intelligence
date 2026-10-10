import os
import sys
import warnings
warnings.filterwarnings("ignore")

import pandas as pd
import numpy as np
from typing import Optional, List
from fastapi import FastAPI, Query, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware

# Append root directory to sys.path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from utils.data_loader import get_cleaned_data, get_dataset_summary, get_column_explanations
from utils.eda_analytics import calculate_kpis, filter_data
from utils.segmentation import load_rfm_data
from utils.market_basket import load_association_rules, recommend_products
from utils.sales_prediction import prepare_daily_sales, train_sales_forecaster, forecast_future_sales
from utils.rag_assistant import get_rag_assistant

app = FastAPI(
    title="AI Retail Intelligence Platform API",
    description="Enterprise REST API and Web Dashboard for Retail Analytics & AI",
    version="2.0.0"
)

# Enable CORS for all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Cached Data Objects
DATA_CACHE = {}

def get_cached_df():
    if "df" not in DATA_CACHE:
        print("Loading cleaned dataset into memory...")
        DATA_CACHE["df"] = get_cleaned_data()
    return DATA_CACHE["df"]

def get_cached_rfm():
    if "rfm" not in DATA_CACHE:
        df = get_cached_df()
        print("Loading RFM customer segmentation...")
        DATA_CACHE["rfm"] = load_rfm_data(df)
    return DATA_CACHE["rfm"]

def get_cached_rules():
    if "rules" not in DATA_CACHE:
        df = get_cached_df()
        print("Loading association rules...")
        DATA_CACHE["rules"] = load_association_rules(df)
    return DATA_CACHE["rules"]

def get_cached_daily():
    if "daily" not in DATA_CACHE:
        df = get_cached_df()
        print("Preparing daily sales data...")
        DATA_CACHE["daily"] = prepare_daily_sales(df)
    return DATA_CACHE["daily"]

def get_cached_rag():
    if "rag" not in DATA_CACHE:
        print("Initializing RAG Assistant...")
        DATA_CACHE["rag"] = get_rag_assistant()
    return DATA_CACHE["rag"]


@app.on_event("startup")
def startup_event():
    print("🚀 Initializing AI Retail Intelligence Backend Server...")
    try:
        get_cached_df()
        get_cached_rfm()
        get_cached_rules()
        get_cached_daily()
        print("✅ Data & Models pre-loaded successfully!")
    except Exception as e:
        print(f"⚠️ Startup warning: {e}")


# ==========================================
# 📊 REST API ENDPOINTS
# ==========================================

@app.get("/api/summary")
def api_summary():
    df = get_cached_df()
    summary = get_dataset_summary(df)
    cols = get_column_explanations()
    return {
        "summary": summary,
        "columns": [{"column": k, "description": v} for k, v in cols.items()]
    }


@app.get("/api/kpis")
def api_kpis(country: Optional[str] = Query(None)):
    df = get_cached_df()
    countries_list = [country] if country and country != "All" else ["All"]
    df_filtered = filter_data(df, countries=countries_list)
    kpis = calculate_kpis(df_filtered)
    
    # Extract unique countries list
    all_countries = ["All"] + sorted(df['Country'].unique().tolist())
    
    return {
        "kpis": kpis,
        "active_records": len(df_filtered),
        "countries": all_countries
    }


@app.get("/api/charts/monthly-revenue")
def api_monthly_revenue(country: Optional[str] = Query(None)):
    df = get_cached_df()
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
    df = get_cached_df()
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
    df = get_cached_df()
    countries_list = [country] if country and country != "All" else ["All"]
    df_filtered = filter_data(df, countries=countries_list)
    
    top_prod = df_filtered.groupby('Description')['TotalPrice'].sum().reset_index()
    top_prod = top_prod.sort_values('TotalPrice', ascending=False).head(top_n)
    top_prod.columns = ['Product', 'Revenue']
    top_prod['Revenue'] = top_prod['Revenue'].round(2)
    
    return top_prod.to_dict(orient="records")


@app.get("/api/charts/top-customers")
def api_top_customers(country: Optional[str] = Query(None), top_n: int = 10):
    df = get_cached_df()
    countries_list = [country] if country and country != "All" else ["All"]
    df_filtered = filter_data(df, countries=countries_list)
    
    top_cust = df_filtered.groupby('CustomerID')['TotalPrice'].sum().reset_index()
    top_cust['CustomerID'] = "ID " + top_cust['CustomerID'].astype(int).astype(str)
    top_cust = top_cust.sort_values('TotalPrice', ascending=False).head(top_n)
    top_cust.columns = ['Customer', 'Revenue']
    top_cust['Revenue'] = top_cust['Revenue'].round(2)
    
    return top_cust.to_dict(orient="records")


@app.get("/api/charts/country-revenue")
def api_country_revenue(top_n: int = 10):
    df = get_cached_df()
    country_df = df.groupby('Country')['TotalPrice'].sum().reset_index()
    country_df = country_df.sort_values('TotalPrice', ascending=False).head(top_n)
    country_df.columns = ['Country', 'Revenue']
    country_df['Revenue'] = country_df['Revenue'].round(2)
    
    return country_df.to_dict(orient="records")


@app.get("/api/charts/weekday-hour")
def api_weekday_hour():
    df = get_cached_df()
    
    # Weekday sales
    weekday_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Sunday']
    df_temp = df.copy()
    weekday_df = df_temp.groupby('Weekday')['TotalPrice'].sum().reindex(weekday_order).reset_index()
    weekday_df.columns = ['Weekday', 'Revenue']
    weekday_df['Revenue'] = weekday_df['Revenue'].round(2)
    
    # Hourly sales
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
    rfm_df = get_cached_rfm()
    
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
    rfm_df = get_cached_rfm()
    cust_res = rfm_df[rfm_df['CustomerID'].astype(str) == customer_id.strip()]
    if cust_res.empty:
        raise HTTPException(status_code=404, detail="Customer ID not found")
    
    row = cust_res.iloc[0].to_dict()
    row['Recency'] = float(row['Recency'])
    row['Frequency'] = float(row['Frequency'])
    row['Monetary'] = round(float(row['Monetary']), 2)
    return row


@app.get("/api/market-basket")
def api_market_basket(min_lift: float = 1.5, top_n: int = 50):
    rules_df = get_cached_rules()
    filtered = rules_df[rules_df['lift'] >= min_lift].sort_values('lift', ascending=False).head(top_n)
    
    records = filtered[['antecedents', 'consequents', 'support', 'confidence', 'lift']].copy()
    records['support'] = (records['support'] * 100).round(2)
    records['confidence'] = (records['confidence'] * 100).round(2)
    records['lift'] = records['lift'].round(2)
    
    stats = {
        "total_rules": len(rules_df),
        "filtered_rules": len(filtered),
        "max_lift": round(float(rules_df['lift'].max()), 2),
        "max_confidence": round(float(rules_df['confidence'].max()) * 100, 2)
    }
    
    return {
        "stats": stats,
        "rules": records.to_dict(orient="records")
    }


@app.get("/api/recommend")
def api_recommend(product: str, top_n: int = 5):
    rules_df = get_cached_rules()
    df = get_cached_df()
    
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
    df = get_cached_df()
    daily_df = get_cached_daily()
    
    eval_res = train_sales_forecaster(df)
    future_df = forecast_future_sales(daily_df, days_ahead=days)
    
    historical = daily_df.tail(60).copy()
    historical['Date'] = historical['Date'].dt.date.astype(str)
    historical['TotalPrice'] = historical['TotalPrice'].round(2)
    
    future = future_df.copy()
    future['Date'] = future['Date'].dt.date.astype(str)
    future['Predicted_Sales'] = future['Predicted_Sales'].round(2)
    
    metrics = {
        "mae": round(eval_res['mae'], 2),
        "rmse": round(eval_res['rmse'], 2),
        "r2": round(eval_res['r2'], 4)
    }
    
    return {
        "metrics": metrics,
        "historical": historical[['Date', 'TotalPrice']].rename(columns={'TotalPrice': 'Revenue'}).to_dict(orient="records"),
        "future": future.to_dict(orient="records")
    }


@app.post("/api/chat")
def api_chat(payload: dict):
    query_text = payload.get("query", "").strip()
    if not query_text:
        return {"response": "Please enter a valid business question."}
    
    try:
        assistant = get_cached_rag()
        response = assistant.query(query_text)
        return {"response": response}
    except Exception as e:
        return {"response": f"Error querying AI assistant: {e}"}


@app.get("/api/search")
def api_search(q: str):
    df = get_cached_df()
    q_str = q.strip().lower()
    
    matching_prods = [p for p in df['Description'].unique() if q_str in p.lower()]
    
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
    df = get_cached_df()
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
