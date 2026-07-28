import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import streamlit as st
from utils.data_loader import get_cleaned_data
from utils.market_basket import load_association_rules, recommend_products

st.set_page_config(page_title="Product Recommendations | AI Retail Platform", layout="wide")
df = get_cleaned_data()
rules_df = load_association_rules(df)

st.title("🤖 Product Recommendation Engine")

all_products = sorted(df['Description'].unique().tolist())
selected_prod = st.selectbox("Select product to get recommendations:", all_products)

if st.button("Generate Recommendations"):
    recs = recommend_products(selected_prod, rules_df, top_n=5)
    if recs:
        st.success(f"Top 5 Recommendations for '{selected_prod}':")
        for i, r in enumerate(recs, 1):
            st.markdown(f"**{i}.** {r}")
    else:
        st.warning("No direct rule match found. Showing popular bestsellers:")
        top_gen = df['Description'].value_counts().head(5).index.tolist()
        for i, r in enumerate(top_gen, 1):
            st.markdown(f"**{i}.** {r}")
