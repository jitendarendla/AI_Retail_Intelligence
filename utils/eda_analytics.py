import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go


def calculate_kpis(df: pd.DataFrame) -> dict:
    """Calculate key performance indicators."""
    total_revenue = float(df['TotalPrice'].sum())
    total_orders = int(df['InvoiceNo'].nunique())
    total_customers = int(df['CustomerID'].nunique())
    total_products = int(df['StockCode'].nunique())
    avg_order_value = float(total_revenue / total_orders) if total_orders > 0 else 0.0
    
    return {
        "total_revenue": total_revenue,
        "total_orders": total_orders,
        "total_customers": total_customers,
        "total_products": total_products,
        "avg_order_value": avg_order_value
    }


def filter_data(df: pd.DataFrame, countries: list = None, date_range: tuple = None) -> pd.DataFrame:
    """Filter dataset by country selection and date range."""
    filtered = df.copy()
    if countries and "All" not in countries:
        filtered = filtered[filtered['Country'].isin(countries)]
    if date_range and len(date_range) == 2:
        start_date, end_date = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
        filtered = filtered[(filtered['InvoiceDate'] >= start_date) & (filtered['InvoiceDate'] <= end_date)]
    return filtered


def fig_monthly_revenue(df: pd.DataFrame):
    """Monthly Revenue Trend."""
    df_temp = df.copy()
    df_temp['YearMonth'] = df_temp['InvoiceDate'].dt.to_period('M').astype(str)
    monthly = df_temp.groupby('YearMonth')['TotalPrice'].sum().reset_index()
    monthly = monthly.sort_values('YearMonth')
    
    fig = px.line(
        monthly, x='YearMonth', y='TotalPrice',
        title="📈 Monthly Revenue Trend",
        labels={"YearMonth": "Month", "TotalPrice": "Revenue (£)"},
        markers=True, text='TotalPrice'
    )
    fig.update_traces(texttemplate='£%{text:,.0f}', textposition='top center', line=dict(width=3, color='#6366F1'))
    fig.update_layout(template="plotly_dark", height=400, margin=dict(l=20, r=20, t=50, b=20))
    return fig


def fig_daily_sales(df: pd.DataFrame):
    """Daily Sales Trend."""
    df_temp = df.copy()
    df_temp['Date'] = df_temp['InvoiceDate'].dt.date
    daily = df_temp.groupby('Date')['TotalPrice'].sum().reset_index()
    
    fig = px.area(
        daily, x='Date', y='TotalPrice',
        title="📅 Daily Sales Trend",
        labels={"Date": "Date", "TotalPrice": "Revenue (£)"}
    )
    fig.update_traces(fillcolor='rgba(99, 102, 241, 0.25)', line=dict(color='#818CF8', width=2))
    fig.update_layout(template="plotly_dark", height=400, margin=dict(l=20, r=20, t=50, b=20))
    return fig


def fig_top_products(df: pd.DataFrame, top_n: int = 10):
    """Top N Products by Revenue."""
    top_p = df.groupby(['Description'])['TotalPrice'].sum().reset_index()
    top_p = top_p.sort_values('TotalPrice', ascending=False).head(top_n)
    
    fig = px.bar(
        top_p, y='Description', x='TotalPrice', orientation='h',
        title=f"🏆 Top {top_n} Products by Revenue",
        labels={"Description": "Product", "TotalPrice": "Revenue (£)"},
        color='TotalPrice', color_continuous_scale='Viridis'
    )
    fig.update_layout(template="plotly_dark", yaxis=dict(autorange="reversed"), height=420, margin=dict(l=20, r=20, t=50, b=20))
    return fig


def fig_top_customers(df: pd.DataFrame, top_n: int = 10):
    """Top N Customers by Revenue."""
    top_c = df.groupby(['CustomerID'])['TotalPrice'].sum().reset_index()
    top_c['CustomerID'] = 'Cust #' + top_c['CustomerID'].astype(str)
    top_c = top_c.sort_values('TotalPrice', ascending=False).head(top_n)
    
    fig = px.bar(
        top_c, x='CustomerID', y='TotalPrice',
        title=f"👑 Top {top_n} High-Value Customers",
        labels={"CustomerID": "Customer ID", "TotalPrice": "Revenue (£)"},
        color='TotalPrice', color_continuous_scale='Plasma'
    )
    fig.update_layout(template="plotly_dark", height=400, margin=dict(l=20, r=20, t=50, b=20))
    return fig


def fig_country_revenue(df: pd.DataFrame, top_n: int = 10):
    """Country-wise Revenue Distribution."""
    country_df = df.groupby('Country')['TotalPrice'].sum().reset_index()
    country_df = country_df.sort_values('TotalPrice', ascending=False).head(top_n)
    
    fig = px.pie(
        country_df, names='Country', values='TotalPrice',
        title=f"🌍 Country-wise Revenue Contribution (Top {top_n})",
        hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel
    )
    fig.update_layout(template="plotly_dark", height=420, margin=dict(l=20, r=20, t=50, b=20))
    return fig


def fig_top_selling_countries(df: pd.DataFrame, top_n: int = 10):
    """Top Selling Countries Bar Chart (Excluding/Including UK)."""
    country_df = df.groupby('Country')['TotalPrice'].sum().reset_index()
    country_df = country_df.sort_values('TotalPrice', ascending=False).head(top_n)
    
    fig = px.bar(
        country_df, x='Country', y='TotalPrice',
        title=f"🌐 Top {top_n} Countries by Sales Volume",
        labels={"Country": "Country", "TotalPrice": "Revenue (£)"},
        color='TotalPrice', color_continuous_scale='Cividis'
    )
    fig.update_layout(template="plotly_dark", height=400, margin=dict(l=20, r=20, t=50, b=20))
    return fig


def fig_revenue_distribution(df: pd.DataFrame):
    """Revenue per Invoice Distribution."""
    inv_rev = df.groupby('InvoiceNo')['TotalPrice'].sum().reset_index()
    # Limit to 99th percentile for clean visualization
    q99 = inv_rev['TotalPrice'].quantile(0.99)
    inv_rev_filtered = inv_rev[inv_rev['TotalPrice'] <= q99]
    
    fig = px.histogram(
        inv_rev_filtered, x='TotalPrice', nbins=50,
        title="📊 Revenue per Order Distribution (99th Percentile Cap)",
        labels={"TotalPrice": "Order Value (£)"},
        color_discrete_sequence=['#10B981']
    )
    fig.update_layout(template="plotly_dark", height=380, margin=dict(l=20, r=20, t=50, b=20))
    return fig


def fig_quantity_distribution(df: pd.DataFrame):
    """Quantity per Order Line Distribution."""
    q99 = df['Quantity'].quantile(0.99)
    qty_filtered = df[df['Quantity'] <= q99]
    
    fig = px.histogram(
        qty_filtered, x='Quantity', nbins=50,
        title="📦 Quantity per Line Item Distribution (99th Percentile Cap)",
        labels={"Quantity": "Item Quantity"},
        color_discrete_sequence=['#F59E0B']
    )
    fig.update_layout(template="plotly_dark", height=380, margin=dict(l=20, r=20, t=50, b=20))
    return fig


def fig_monthly_orders(df: pd.DataFrame):
    """Monthly Orders Volume."""
    df_temp = df.copy()
    df_temp['YearMonth'] = df_temp['InvoiceDate'].dt.to_period('M').astype(str)
    monthly_orders = df_temp.groupby('YearMonth')['InvoiceNo'].nunique().reset_index()
    
    fig = px.bar(
        monthly_orders, x='YearMonth', y='InvoiceNo',
        title="🛍️ Monthly Orders Volume",
        labels={"YearMonth": "Month", "InvoiceNo": "Total Unique Orders"},
        color_discrete_sequence=['#3B82F6']
    )
    fig.update_layout(template="plotly_dark", height=380, margin=dict(l=20, r=20, t=50, b=20))
    return fig


def fig_revenue_by_weekday(df: pd.DataFrame):
    """Revenue by Weekday."""
    days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    weekday_rev = df.groupby('Weekday')['TotalPrice'].sum().reindex(days_order).dropna().reset_index()
    
    fig = px.bar(
        weekday_rev, x='Weekday', y='TotalPrice',
        title="📅 Sales Revenue by Day of Week",
        labels={"Weekday": "Day of Week", "TotalPrice": "Revenue (£)"},
        color='TotalPrice', color_continuous_scale='Teal'
    )
    fig.update_layout(template="plotly_dark", height=380, margin=dict(l=20, r=20, t=50, b=20))
    return fig


def fig_revenue_by_hour(df: pd.DataFrame):
    """Revenue by Hour of Day."""
    hour_rev = df.groupby('Hour')['TotalPrice'].sum().reset_index()
    
    fig = px.line(
        hour_rev, x='Hour', y='TotalPrice',
        title="⏰ Sales Revenue by Hour of Day",
        labels={"Hour": "Hour (0 - 23)", "TotalPrice": "Revenue (£)"},
        markers=True
    )
    fig.update_traces(line=dict(color='#EC4899', width=3))
    fig.update_layout(template="plotly_dark", height=380, margin=dict(l=20, r=20, t=50, b=20))
    return fig
