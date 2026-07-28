import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import streamlit as st
from utils.data_loader import get_cleaned_data, get_dataset_summary, get_column_explanations
from utils.eda_analytics import (fig_revenue_by_weekday, fig_revenue_by_hour, fig_monthly_orders,
                                 fig_country_revenue, fig_top_selling_countries,
                                 fig_revenue_distribution, fig_quantity_distribution)

st.set_page_config(page_title="Sales Analytics | AI Retail Platform", layout="wide")
df = get_cleaned_data()

st.title("📈 Detailed Sales Analytics & Understanding")

tab1, tab2, tab3 = st.tabs(["📊 Temporal Dynamics", "🌍 Geographical & Distribution", "📋 Data Understanding"])

with tab1:
    st.plotly_chart(fig_revenue_by_weekday(df), use_container_width=True)
    st.plotly_chart(fig_revenue_by_hour(df), use_container_width=True)
    st.plotly_chart(fig_monthly_orders(df), use_container_width=True)

with tab2:
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(fig_country_revenue(df), use_container_width=True)
    with col2:
        st.plotly_chart(fig_top_selling_countries(df), use_container_width=True)
        
    col3, col4 = st.columns(2)
    with col3:
        st.plotly_chart(fig_revenue_distribution(df), use_container_width=True)
    with col4:
        st.plotly_chart(fig_quantity_distribution(df), use_container_width=True)

with tab3:
    summary = get_dataset_summary(df)
    st.markdown("### Dataset Overview")
    st.json(summary)
    st.markdown("### Column Explanations")
    st.dataframe(get_column_explanations(), use_container_width=True)
