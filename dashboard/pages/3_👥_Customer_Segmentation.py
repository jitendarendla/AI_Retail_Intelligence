import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import streamlit as st
from utils.data_loader import get_cleaned_data
from utils.segmentation import load_rfm_data, fig_rfm_3d_scatter, fig_segment_distribution, fig_segment_revenue

st.set_page_config(page_title="Customer Segmentation | AI Retail Platform", layout="wide")
df = get_cleaned_data()
rfm_df = load_rfm_data(df)

st.title("👥 RFM Customer Segmentation (KMeans)")

col1, col2 = st.columns(2)
with col1:
    st.plotly_chart(fig_segment_distribution(rfm_df), use_container_width=True)
with col2:
    st.plotly_chart(fig_segment_revenue(rfm_df), use_container_width=True)

st.plotly_chart(fig_rfm_3d_scatter(rfm_df), use_container_width=True)

st.markdown("### RFM Customer Dataset")
st.dataframe(rfm_df, use_container_width=True)
