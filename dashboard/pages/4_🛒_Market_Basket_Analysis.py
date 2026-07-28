import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import streamlit as st
from utils.data_loader import get_cleaned_data
from utils.market_basket import load_association_rules, fig_association_rules_scatter, fig_top_lift_rules_bar

st.set_page_config(page_title="Market Basket Analysis | AI Retail Platform", layout="wide")
df = get_cleaned_data()
rules_df = load_association_rules(df)

st.title("🛒 Market Basket Analysis (Apriori)")

st.plotly_chart(fig_top_lift_rules_bar(rules_df, top_n=15), use_container_width=True)
st.plotly_chart(fig_association_rules_scatter(rules_df, top_n=50), use_container_width=True)

st.markdown("### Association Rules Table")
st.dataframe(rules_df[['antecedents', 'consequents', 'support', 'confidence', 'lift']], use_container_width=True)
