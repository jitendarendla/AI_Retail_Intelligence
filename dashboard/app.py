import os
import sys
import warnings
warnings.filterwarnings("ignore")

import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

# Add workspace path to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.data_loader import get_cleaned_data, get_dataset_summary, get_column_explanations
from utils.eda_analytics import (calculate_kpis, filter_data, fig_monthly_revenue, fig_daily_sales,
                                 fig_top_products, fig_top_customers, fig_country_revenue,
                                 fig_top_selling_countries, fig_revenue_distribution,
                                 fig_quantity_distribution, fig_monthly_orders,
                                 fig_revenue_by_weekday, fig_revenue_by_hour)
from utils.segmentation import load_rfm_data, fig_rfm_3d_scatter, fig_segment_distribution, fig_segment_revenue
from utils.market_basket import load_association_rules, recommend_products, fig_association_rules_scatter, fig_top_lift_rules_bar
from utils.sales_prediction import prepare_daily_sales, train_sales_forecaster, forecast_future_sales, fig_actual_vs_predicted, fig_future_forecast
from utils.rag_assistant import get_rag_assistant

# Page Config
st.set_page_config(
    page_title="AI Retail Intelligence Platform | Enterprise Suite",
    page_icon="🛍️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Masterpiece Glassmorphism CSS Styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    
    /* Main Canvas Background */
    .stApp {
        background: radial-gradient(circle at 10% 10%, #0F172A 0%, #090D16 50%, #030712 100%);
        color: #F8FAFC;
    }

    /* Padding adjustments */
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 3rem;
    }

    /* Hero Banner Header */
    .hero-banner {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.8) 0%, rgba(15, 23, 42, 0.95) 100%);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.12);
        border-radius: 20px;
        padding: 26px 32px;
        margin-bottom: 24px;
        position: relative;
        overflow: hidden;
        box-shadow: 0 20px 50px rgba(0, 0, 0, 0.5);
    }
    .hero-banner::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0; height: 4px;
        background: linear-gradient(90deg, #6366F1, #8B5CF6, #EC4899, #10B981, #F59E0B);
    }
    .hero-title {
        font-size: 2.35rem;
        font-weight: 800;
        background: linear-gradient(90deg, #818CF8 0%, #C084FC 50%, #F472B6 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0 0 6px 0;
        letter-spacing: -0.02em;
    }
    .hero-subtitle {
        font-size: 1.05rem;
        color: #94A3B8;
        margin: 0;
        font-weight: 500;
    }

    /* Status Pills */
    .pill {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 5px 14px;
        border-radius: 9999px;
        font-size: 0.78rem;
        font-weight: 700;
        letter-spacing: 0.04em;
        text-transform: uppercase;
        margin-right: 8px;
        margin-top: 14px;
    }
    .pill-indigo { background: rgba(99, 102, 241, 0.18); color: #818CF8; border: 1px solid rgba(99, 102, 241, 0.4); }
    .pill-emerald { background: rgba(16, 185, 129, 0.18); color: #34D399; border: 1px solid rgba(16, 185, 129, 0.4); }
    .pill-pink { background: rgba(236, 72, 153, 0.18); color: #F472B6; border: 1px solid rgba(236, 72, 153, 0.4); }
    .pill-amber { background: rgba(245, 158, 11, 0.18); color: #FBBF24; border: 1px solid rgba(245, 158, 11, 0.4); }

    /* Ultra Metric Cards */
    .metric-card {
        background: linear-gradient(145deg, rgba(30, 41, 59, 0.7), rgba(15, 23, 42, 0.85));
        backdrop-filter: blur(16px);
        border: 1px solid rgba(255, 255, 255, 0.09);
        border-radius: 18px;
        padding: 22px 18px;
        text-align: center;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
    }
    .metric-card:hover {
        transform: translateY(-6px);
        border-color: rgba(129, 140, 248, 0.6);
        box-shadow: 0 16px 40px rgba(99, 102, 241, 0.35);
    }
    .metric-icon {
        font-size: 2.1rem;
        margin-bottom: 6px;
    }
    .metric-val {
        font-size: 1.85rem;
        font-weight: 800;
        color: #F8FAFC;
        letter-spacing: -0.02em;
        margin: 4px 0;
    }
    .metric-lbl {
        font-size: 0.82rem;
        font-weight: 700;
        text-transform: uppercase;
        color: #94A3B8;
        letter-spacing: 0.06em;
    }
    .metric-sub {
        font-size: 0.76rem;
        font-weight: 600;
        color: #10B981;
        margin-top: 4px;
    }

    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #050811;
        border-right: 1px solid rgba(255, 255, 255, 0.08);
    }

    /* Custom Streamlit Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 48px;
        white-space: pre-wrap;
        border-radius: 12px;
        background-color: rgba(30, 41, 59, 0.5);
        color: #94A3B8;
        font-weight: 600;
        padding: 0 22px;
        border: 1px solid rgba(255, 255, 255, 0.06);
        transition: all 0.2s ease;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(90deg, #4F46E5, #7C3AED) !important;
        color: #FFFFFF !important;
        border-color: rgba(129, 140, 248, 0.6) !important;
        box-shadow: 0 6px 20px rgba(99, 102, 241, 0.4);
    }

    /* Persona Cards */
    .persona-card {
        border-radius: 16px;
        padding: 22px;
        color: white;
        margin-bottom: 16px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.3);
    }
    .vip-bg { background: linear-gradient(135deg, #064E3B 0%, #047857 100%); border: 1px solid #10B981; }
    .loyal-bg { background: linear-gradient(135deg, #1E3A8A 0%, #1D4ED8 100%); border: 1px solid #3B82F6; }
    .reg-bg { background: linear-gradient(135deg, #78350F 0%, #B45309 100%); border: 1px solid #F59E0B; }
    .risk-bg { background: linear-gradient(135deg, #7F1D1D 0%, #B91C1C 100%); border: 1px solid #EF4444; }

    /* Product Cards */
    .prod-card {
        background: linear-gradient(145deg, rgba(30, 41, 59, 0.8), rgba(15, 23, 42, 0.95));
        border: 1px solid rgba(129, 140, 248, 0.25);
        border-radius: 16px;
        padding: 20px;
        transition: transform 0.2s;
    }
    .prod-card:hover {
        transform: translateY(-5px);
        border-color: #818CF8;
        box-shadow: 0 10px 25px rgba(99, 102, 241, 0.3);
    }
</style>
""", unsafe_allow_html=True)


@st.cache_data(show_spinner=False)
def load_data():
    return get_cleaned_data()


def apply_plotly_theme(fig):
    """Apply unified dark glassmorphism styling to Plotly figures."""
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family='Plus Jakarta Sans, sans-serif', color='#CBD5E1'),
        title=dict(font=dict(size=16, color='#F8FAFC', family='Plus Jakarta Sans')),
        legend=dict(font=dict(color='#94A3B8')),
        xaxis=dict(gridcolor='rgba(255, 255, 255, 0.05)', zerolinecolor='rgba(255, 255, 255, 0.1)'),
        yaxis=dict(gridcolor='rgba(255, 255, 255, 0.05)', zerolinecolor='rgba(255, 255, 255, 0.1)'),
        margin=dict(l=20, r=20, t=50, b=20)
    )
    return fig


def main():
    # Load dataset
    try:
        df = load_data()
    except Exception as e:
        st.error(f"⚠️ Error loading cleaned dataset: {e}. Please run `python run_pipeline.py` first.")
        st.stop()

    # Sidebar Navigation & Branding
    st.sidebar.markdown("""
    <div style="text-align: center; padding: 12px 0;">
        <h2 style="margin: 0; font-size: 1.8rem; background: linear-gradient(90deg, #818CF8, #C084FC); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
            🛍️ RETAIL AI
        </h2>
        <p style="font-size: 0.8rem; color: #94A3B8; margin-top: 4px; font-weight: 600;">Executive Intelligence Suite</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.sidebar.markdown("---")
    
    navigation = st.sidebar.radio(
        "PLATFORM MODULES",
        [
            "🏠 Executive Dashboard",
            "📈 Sales & Market Analytics",
            "👥 RFM Customer Segmentation",
            "🛒 Market Basket Analysis",
            "🤖 Product Recommender",
            "📊 Sales Prediction (RF)",
            "💬 RAG AI Assistant",
            "📄 Export Reports"
        ]
    )
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("🎛️ Interactive Filters")
    
    # Country Filter
    countries = ["All"] + sorted(df['Country'].unique().tolist())
    selected_countries = st.sidebar.multiselect("Country Filter", countries, default=["All"])
    
    # Date Range Filter
    min_date = df['InvoiceDate'].min().date()
    max_date = df['InvoiceDate'].max().date()
    selected_dates = st.sidebar.date_input(
        "Date Horizon",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )
    
    # Apply Filters
    df_filtered = filter_data(df, countries=selected_countries, date_range=selected_dates)
    
    st.sidebar.markdown("---")
    st.sidebar.markdown(f"""
    <div style="background: rgba(30, 41, 59, 0.6); padding: 14px; border-radius: 12px; border: 1px solid rgba(255,255,255,0.08); font-size: 0.82rem; color: #94A3B8;">
        <div style="margin-bottom:6px;">📊 Active Records: <strong style="color:#818CF8;">{len(df_filtered):,}</strong></div>
        <div style="margin-bottom:6px;">🌍 Unique Countries: <strong style="color:#34D399;">{df_filtered['Country'].nunique()}</strong></div>
        <div>🗓️ Date Span: <strong>{min_date} ➔ {max_date}</strong></div>
    </div>
    """, unsafe_allow_html=True)

    # Quick Search Bar in Top Header
    with st.expander("🔍 Quick Product / SKU Instant Search", expanded=False):
        all_prods = sorted(df['Description'].unique().tolist())
        search_item = st.selectbox("Type to search any product in catalog:", [""] + all_prods, index=0)
        if search_item:
            item_df = df[df['Description'] == search_item]
            s1, s2, s3, s4 = st.columns(4)
            s1.metric("Total Revenue", f"£{item_df['TotalPrice'].sum():,.2f}")
            s2.metric("Total Units Sold", f"{item_df['Quantity'].sum():,}")
            s3.metric("Distinct Customers", f"{item_df['CustomerID'].nunique():,}")
            s4.metric("Average Price", f"£{item_df['UnitPrice'].mean():.2f}")

    # ==========================================
    # 🏠 1. EXECUTIVE DASHBOARD
    # ==========================================
    if navigation == "🏠 Executive Dashboard":
        st.markdown("""
        <div class="hero-banner">
            <h1 class="hero-title">AI Retail Intelligence Platform</h1>
            <p class="hero-subtitle">Real-Time Revenue Analytics, RFM Segmentation, Association Mining & Predictive Forecasting</p>
            <div>
                <span class="pill pill-indigo">⚡ Live Pipeline Ready</span>
                <span class="pill pill-emerald">👥 4,338 Customer Accounts</span>
                <span class="pill pill-pink">🛒 1,030 Association Rules</span>
                <span class="pill pill-amber">🔮 RF Sales Predictor</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Calculate KPIs
        kpis = calculate_kpis(df_filtered)
        
        c1, c2, c3, c4, c5 = st.columns(5)
        with c1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-icon">💰</div>
                <div class="metric-val">£{kpis['total_revenue']:,.0f}</div>
                <div class="metric-lbl">Total Revenue</div>
                <div class="metric-sub">▲ 100% Verified</div>
            </div>
            """, unsafe_allow_html=True)
        with c2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-icon">📦</div>
                <div class="metric-val">{kpis['total_orders']:,}</div>
                <div class="metric-lbl">Total Orders</div>
                <div class="metric-sub">▲ Unique Invoices</div>
            </div>
            """, unsafe_allow_html=True)
        with c3:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-icon">👥</div>
                <div class="metric-val">{kpis['total_customers']:,}</div>
                <div class="metric-lbl">Active Customers</div>
                <div class="metric-sub">▲ Accounts</div>
            </div>
            """, unsafe_allow_html=True)
        with c4:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-icon">🏷️</div>
                <div class="metric-val">{kpis['total_products']:,}</div>
                <div class="metric-lbl">Catalog Products</div>
                <div class="metric-sub">▲ Unique SKUs</div>
            </div>
            """, unsafe_allow_html=True)
        with c5:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-icon">💳</div>
                <div class="metric-val">£{kpis['avg_order_value']:.2f}</div>
                <div class="metric-lbl">Avg Order Value</div>
                <div class="metric-sub">▲ Per Basket</div>
            </div>
            """, unsafe_allow_html=True)
            
        st.markdown("<br>", unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            fig1 = fig_monthly_revenue(df_filtered)
            st.plotly_chart(apply_plotly_theme(fig1), use_container_width=True)
        with col2:
            fig2 = fig_daily_sales(df_filtered)
            st.plotly_chart(apply_plotly_theme(fig2), use_container_width=True)
            
        col3, col4 = st.columns(2)
        with col3:
            fig3 = fig_top_products(df_filtered, top_n=10)
            st.plotly_chart(apply_plotly_theme(fig3), use_container_width=True)
        with col4:
            fig4 = fig_top_customers(df_filtered, top_n=10)
            st.plotly_chart(apply_plotly_theme(fig4), use_container_width=True)

    # ==========================================
    # 📈 2. SALES & MARKET ANALYTICS
    # ==========================================
    elif navigation == "📈 Sales & Market Analytics":
        st.markdown("""
        <div class="hero-banner">
            <h1 class="hero-title">Sales Analytics & Data Understanding</h1>
            <p class="hero-subtitle">Deep-dive analysis into weekday trends, peak hours, country distributions, and dataset schemas.</p>
        </div>
        """, unsafe_allow_html=True)
        
        tab1, tab2, tab3 = st.tabs(["⏰ Temporal Trends", "🌍 Geographic & Distribution", "📋 Dataset Audit"])
        
        with tab1:
            c1, c2 = st.columns(2)
            with c1:
                st.plotly_chart(apply_plotly_theme(fig_revenue_by_weekday(df_filtered)), use_container_width=True)
            with c2:
                st.plotly_chart(apply_plotly_theme(fig_revenue_by_hour(df_filtered)), use_container_width=True)
            st.plotly_chart(apply_plotly_theme(fig_monthly_orders(df_filtered)), use_container_width=True)
            
        with tab2:
            col1, col2 = st.columns(2)
            with col1:
                st.plotly_chart(apply_plotly_theme(fig_country_revenue(df_filtered)), use_container_width=True)
            with col2:
                st.plotly_chart(apply_plotly_theme(fig_top_selling_countries(df_filtered)), use_container_width=True)
                
            col3, col4 = st.columns(2)
            with col3:
                st.plotly_chart(apply_plotly_theme(fig_revenue_distribution(df_filtered)), use_container_width=True)
            with col4:
                st.plotly_chart(apply_plotly_theme(fig_quantity_distribution(df_filtered)), use_container_width=True)
                
        with tab3:
            st.subheader("Module 1 Dataset Summary")
            summary = get_dataset_summary(df)
            
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Rows × Columns", f"{summary['num_rows']:,} × {summary['num_columns']}")
            c2.metric("Duplicate Rows Dropped", f"{summary['duplicate_rows']:,}")
            c3.metric("Missing Customer IDs", f"{summary['missing_values'].get('CustomerID', 0):,}")
            c4.metric("Clean Line Items", f"{len(df):,}")
            
            st.markdown("### Schema Definitions")
            cols_def = get_column_explanations()
            st.dataframe(pd.DataFrame(list(cols_def.items()), columns=["Column Name", "Description / Purpose"]), use_container_width=True)

    # ==========================================
    # 👥 3. CUSTOMER RFM SEGMENTATION
    # ==========================================
    elif navigation == "👥 RFM Customer Segmentation":
        st.markdown("""
        <div class="hero-banner">
            <h1 class="hero-title">RFM Customer Segmentation (KMeans)</h1>
            <p class="hero-subtitle">Machine Learning Customer Profiling into VIP, Loyal, Regular, and At-Risk account personas.</p>
        </div>
        """, unsafe_allow_html=True)
        
        with st.spinner("Loading Customer Segments..."):
            rfm_df = load_rfm_data(df)
            
        # Persona Cards Row
        c1, c2, c3, c4 = st.columns(4)
        vips = rfm_df[rfm_df['Segment'] == 'VIP Customers']
        loyals = rfm_df[rfm_df['Segment'] == 'Loyal Customers']
        regs = rfm_df[rfm_df['Segment'] == 'Regular Customers']
        risks = rfm_df[rfm_df['Segment'] == 'At Risk Customers']
        
        with c1:
            st.markdown(f"""
            <div class="persona-card vip-bg">
                <h3>👑 VIP Customers</h3>
                <h2 style="margin: 4px 0; font-size: 2.2rem;">{len(vips):,}</h2>
                <p style="font-size: 0.88rem; margin:0;">Spend: £{vips['Monetary'].sum():,.0f}<br>Strategy: Exclusive Perks & Direct Manager</p>
            </div>
            """, unsafe_allow_html=True)
        with c2:
            st.markdown(f"""
            <div class="persona-card loyal-bg">
                <h3>💎 Loyal Customers</h3>
                <h2 style="margin: 4px 0; font-size: 2.2rem;">{len(loyals):,}</h2>
                <p style="font-size: 0.88rem; margin:0;">Spend: £{loyals['Monetary'].sum():,.0f}<br>Strategy: Cross-sell & Loyalty Rewards</p>
            </div>
            """, unsafe_allow_html=True)
        with c3:
            st.markdown(f"""
            <div class="persona-card reg-bg">
                <h3>🎯 Regular Customers</h3>
                <h2 style="margin: 4px 0; font-size: 2.2rem;">{len(regs):,}</h2>
                <p style="font-size: 0.88rem; margin:0;">Spend: £{regs['Monetary'].sum():,.0f}<br>Strategy: Engagement Offers & Discounts</p>
            </div>
            """, unsafe_allow_html=True)
        with c4:
            st.markdown(f"""
            <div class="persona-card risk-bg">
                <h3>⚠️ At Risk Customers</h3>
                <h2 style="margin: 4px 0; font-size: 2.2rem;">{len(risks):,}</h2>
                <p style="font-size: 0.88rem; margin:0;">Spend: £{risks['Monetary'].sum():,.0f}<br>Strategy: Win-back Email Campaigns</p>
            </div>
            """, unsafe_allow_html=True)
            
        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(apply_plotly_theme(fig_segment_distribution(rfm_df)), use_container_width=True)
        with col2:
            st.plotly_chart(apply_plotly_theme(fig_segment_revenue(rfm_df)), use_container_width=True)
            
        st.plotly_chart(apply_plotly_theme(fig_rfm_3d_scatter(rfm_df)), use_container_width=True)
        
        st.subheader("🔍 Customer Segment Account Lookup")
        cust_search = st.text_input("Type Customer ID to look up account segment (e.g. 17850):")
        if cust_search:
            res_cust = rfm_df[rfm_df['CustomerID'].astype(str) == cust_search.strip()]
            if not res_cust.empty:
                st.success(f"Customer #{cust_search} Details:")
                st.dataframe(res_cust, use_container_width=True)
            else:
                st.warning(f"Customer ID #{cust_search} not found.")

    # ==========================================
    # 🛒 4. MARKET BASKET ANALYSIS
    # ==========================================
    elif navigation == "🛒 Market Basket Analysis":
        st.markdown("""
        <div class="hero-banner">
            <h1 class="hero-title">Market Basket Analysis (FP-Growth)</h1>
            <p class="hero-subtitle">Uncover high-lift association rules and product purchasing co-occurrences.</p>
        </div>
        """, unsafe_allow_html=True)
        
        rules_df = load_association_rules(df)
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Mined Association Rules", f"{len(rules_df):,}")
        c2.metric("Max Lift Score", f"{rules_df['lift'].max():.2f}")
        c3.metric("Max Rule Confidence", f"{rules_df['confidence'].max():.2%}")
        
        min_lift_val = st.slider("Filter by Minimum Lift Score:", 1.0, float(rules_df['lift'].max()), 2.0)
        rules_filtered = rules_df[rules_df['lift'] >= min_lift_val]
        
        st.plotly_chart(apply_plotly_theme(fig_top_lift_rules_bar(rules_filtered, top_n=15)), use_container_width=True)
        st.plotly_chart(apply_plotly_theme(fig_association_rules_scatter(rules_filtered, top_n=50)), use_container_width=True)
        
        st.markdown("### Association Rules Data Table")
        st.dataframe(rules_filtered[['antecedents', 'consequents', 'support', 'confidence', 'lift']], use_container_width=True)

    # ==========================================
    # 🤖 5. PRODUCT RECOMMENDER
    # ==========================================
    elif navigation == "🤖 Product Recommender":
        st.markdown("""
        <div class="hero-banner">
            <h1 class="hero-title">AI Cross-Selling Product Recommender</h1>
            <p class="hero-subtitle">Select any product to get Top 5 cross-selling recommendations derived from mined association rules.</p>
        </div>
        """, unsafe_allow_html=True)
        
        rules_df = load_association_rules(df)
        all_products = sorted(df['Description'].unique().tolist())
        
        selected_prod = st.selectbox("Search or Select Target Product:", all_products, index=0)
        
        if st.button("🚀 Find Top 5 Recommendations"):
            recs = recommend_products(selected_prod, rules_df, top_n=5)
            
            if recs:
                st.success(f"Top 5 Cross-Selling Recommendations for **{selected_prod}**:")
                cols = st.columns(5)
                for idx, r_item in enumerate(recs):
                    with cols[idx]:
                        st.markdown(f"""
                        <div class="prod-card">
                            <div style="font-size:0.78rem; font-weight:800; color:#A78BFA; text-transform:uppercase;">Recommendation #{idx+1}</div>
                            <div style="font-size:0.92rem; font-weight:700; color:#F8FAFC; margin-top:8px; min-height:46px;">{r_item}</div>
                            <div style="font-size:0.8rem; color:#10B981; margin-top:8px;">✔ High Lift Co-Purchase</div>
                        </div>
                        """, unsafe_allow_html=True)
            else:
                st.warning(f"No direct rule match for **{selected_prod}**. Showing top bestsellers:")
                top_gen = df['Description'].value_counts().head(5).index.tolist()
                cols = st.columns(5)
                for idx, r_item in enumerate(top_gen):
                    with cols[idx]:
                        st.markdown(f"""
                        <div class="prod-card">
                            <div style="font-size:0.78rem; font-weight:800; color:#F59E0B; text-transform:uppercase;">Bestseller #{idx+1}</div>
                            <div style="font-size:0.92rem; font-weight:700; color:#F8FAFC; margin-top:8px; min-height:46px;">{r_item}</div>
                            <div style="font-size:0.8rem; color:#F59E0B; margin-top:8px;">🔥 High Volume Item</div>
                        </div>
                        """, unsafe_allow_html=True)

    # ==========================================
    # 📊 6. SALES PREDICTION (RF)
    # ==========================================
    elif navigation == "📊 Sales Prediction (RF)":
        st.markdown("""
        <div class="hero-banner">
            <h1 class="hero-title">Daily Sales Prediction (Random Forest)</h1>
            <p class="hero-subtitle">Supervised Machine Learning model for daily revenue forecasting and interactive future horizon predictions.</p>
        </div>
        """, unsafe_allow_html=True)
        
        eval_res = train_sales_forecaster(df)
        daily_df = prepare_daily_sales(df)
        
        c1, c2, c3 = st.columns(3)
        c1.metric("MAE (Mean Absolute Error)", f"£{eval_res['mae']:,.2f}")
        c2.metric("RMSE (Root Mean Sq Error)", f"£{eval_res['rmse']:,.2f}")
        c3.metric("R² Accuracy Score", f"{eval_res['r2']:.4f}")
        
        st.plotly_chart(apply_plotly_theme(fig_actual_vs_predicted(eval_res)), use_container_width=True)
        
        st.markdown("---")
        st.subheader("🔮 Interactive Future Sales Horizon")
        horizon = st.slider("Select Forecast Days Ahead:", 1, 60, 14)
        
        future_df = forecast_future_sales(daily_df, days_ahead=horizon)
        st.plotly_chart(apply_plotly_theme(fig_future_forecast(daily_df, future_df)), use_container_width=True)
        st.dataframe(future_df, use_container_width=True)

    # ==========================================
    # 💬 7. RAG AI ASSISTANT
    # ==========================================
    elif navigation == "💬 RAG AI Assistant":
        st.markdown("""
        <div class="hero-banner">
            <h1 class="hero-title">RAG AI Retail Assistant</h1>
            <p class="hero-subtitle">Natural Language Business Querying powered by FAISS Vector Database and Sentence Transformers.</p>
        </div>
        """, unsafe_allow_html=True)
        
        assistant = get_rag_assistant()
        
        if "messages" not in st.session_state:
            st.session_state.messages = [
                {"role": "assistant", "content": "Hello! I am your AI Retail Assistant. Ask me anything about revenue, top products, customer spending, or recommendations!"}
            ]
            
        for msg in st.session_state.messages:
            st.chat_message(msg["role"]).write(msg["content"])
            
        user_input = st.chat_input("Ask a business question (e.g. Which products generated highest revenue?)...")
        if user_input:
            st.session_state.messages.append({"role": "user", "content": user_input})
            st.chat_message("user").write(user_input)
            
            with st.spinner("Searching FAISS vector database..."):
                response = assistant.query(user_input)
                
            st.session_state.messages.append({"role": "assistant", "content": response})
            st.chat_message("assistant").write(response)

    # ==========================================
    # 📄 8. EXPORT REPORTS
    # ==========================================
    elif navigation == "📄 Export Reports":
        st.markdown("""
        <div class="hero-banner">
            <h1 class="hero-title">Exportable Analytics & Model Reports</h1>
            <p class="hero-subtitle">Download clean CSV reports for business reporting, executive slides, and audits.</p>
        </div>
        """, unsafe_allow_html=True)
        
        rfm_df = load_rfm_data(df)
        rules_df = load_association_rules(df)
        daily_df = prepare_daily_sales(df)
        future_df = forecast_future_sales(daily_df, days_ahead=14)
        
        c1, c2 = st.columns(2)
        with c1:
            st.download_button("📥 Download Cleaned Dataset (CSV)", df.to_csv(index=False).encode('utf-8'), "cleaned_retail_data.csv", "text/csv", use_container_width=True)
            st.markdown("<br>", unsafe_allow_html=True)
            st.download_button("📥 Download Customer Segments RFM (CSV)", rfm_df.to_csv(index=False).encode('utf-8'), "customer_segments_rfm.csv", "text/csv", use_container_width=True)
        with c2:
            st.download_button("📥 Download Association Rules (CSV)", rules_df.to_csv(index=False).encode('utf-8'), "association_rules.csv", "text/csv", use_container_width=True)
            st.markdown("<br>", unsafe_allow_html=True)
            st.download_button("📥 Download 14-Day Sales Forecast (CSV)", future_df.to_csv(index=False).encode('utf-8'), "sales_forecast_14days.csv", "text/csv", use_container_width=True)


if __name__ == "__main__":
    main()
