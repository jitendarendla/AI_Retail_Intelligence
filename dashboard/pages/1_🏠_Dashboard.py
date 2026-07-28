import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import streamlit as st
from utils.data_loader import get_cleaned_data
from utils.eda_analytics import calculate_kpis, fig_monthly_revenue, fig_daily_sales, fig_top_products, fig_top_customers

st.set_page_config(page_title="Dashboard | AI Retail Platform", layout="wide")

df = get_cleaned_data()
kpis = calculate_kpis(df)

st.title("🏠 Executive Sales Dashboard")

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Total Revenue", f"£{kpis['total_revenue']:,.0f}")
c2.metric("Total Orders", f"{kpis['total_orders']:,}")
c3.metric("Total Customers", f"{kpis['total_customers']:,}")
c4.metric("Total Products", f"{kpis['total_products']:,}")
c5.metric("Avg Order Value", f"£{kpis['avg_order_value']:.2f}")

st.markdown("---")
col1, col2 = st.columns(2)
with col1:
    st.plotly_chart(fig_monthly_revenue(df), use_container_width=True)
with col2:
    st.plotly_chart(fig_daily_sales(df), use_container_width=True)

col3, col4 = st.columns(2)
with col3:
    st.plotly_chart(fig_top_products(df), use_container_width=True)
with col4:
    st.plotly_chart(fig_top_customers(df), use_container_width=True)
