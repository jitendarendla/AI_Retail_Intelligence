import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import streamlit as st
from utils.data_loader import get_cleaned_data
from utils.sales_prediction import prepare_daily_sales, train_sales_forecaster, forecast_future_sales, fig_actual_vs_predicted, fig_future_forecast

st.set_page_config(page_title="Sales Prediction | AI Retail Platform", layout="wide")
df = get_cleaned_data()
eval_res = train_sales_forecaster(df)
daily_df = prepare_daily_sales(df)

st.title("📊 Sales Revenue Forecasting")

c1, c2, c3 = st.columns(3)
c1.metric("MAE", f"£{eval_res['mae']:,.2f}")
c2.metric("RMSE", f"£{eval_res['rmse']:,.2f}")
c3.metric("R² Score", f"{eval_res['r2']:.4f}")

st.plotly_chart(fig_actual_vs_predicted(eval_res), use_container_width=True)

horizon = st.slider("Forecast Days Ahead:", 1, 30, 14)
future_df = forecast_future_sales(daily_df, days_ahead=horizon)
st.plotly_chart(fig_future_forecast(daily_df, future_df), use_container_width=True)
st.dataframe(future_df, use_container_width=True)
