import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import streamlit as st
from utils.data_loader import get_cleaned_data
from utils.segmentation import load_rfm_data
from utils.market_basket import load_association_rules
from utils.sales_prediction import prepare_daily_sales, forecast_future_sales

st.set_page_config(page_title="Reports | AI Retail Platform", layout="wide")
st.title("📄 Exportable Analytics & Reports")

df = get_cleaned_data()
rfm_df = load_rfm_data(df)
rules_df = load_association_rules(df)
daily_df = prepare_daily_sales(df)
future_df = forecast_future_sales(daily_df, days_ahead=14)

c1, c2 = st.columns(2)
with c1:
    st.download_button("Download Cleaned Dataset (CSV)", df.to_csv(index=False).encode('utf-8'), "cleaned_retail_data.csv", "text/csv")
    st.download_button("Download RFM Segments (CSV)", rfm_df.to_csv(index=False).encode('utf-8'), "customer_segments_rfm.csv", "text/csv")
with c2:
    st.download_button("Download Association Rules (CSV)", rules_df.to_csv(index=False).encode('utf-8'), "association_rules.csv", "text/csv")
    st.download_button("Download 14-Day Sales Forecast (CSV)", future_df.to_csv(index=False).encode('utf-8'), "sales_forecast_14days.csv", "text/csv")
