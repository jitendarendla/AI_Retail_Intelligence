import os
import pandas as pd
import numpy as np
try:
    from sklearn.preprocessing import StandardScaler
except Exception:
    class StandardScaler:
        def fit_transform(self, X):
            if hasattr(X, 'values'):
                X = X.values
            return (X - X.mean(axis=0)) / (X.std(axis=0) + 1e-8)
        def transform(self, X):
            return self.fit_transform(X)

try:
    from sklearn.cluster import KMeans
except Exception as e:
    print(f"Notice: sklearn.cluster.KMeans DLL blocked by system policy ({e}). Using SciPy FallbackKMeans.")
    from scipy.cluster.vq import kmeans2
    
    class KMeans:
        def __init__(self, n_clusters=4, random_state=42, n_init=10):
            self.n_clusters = n_clusters
            self.random_state = random_state
            self.cluster_centers_ = None
            
        def fit_predict(self, X):
            if hasattr(X, "values"):
                X = X.values
            np.random.seed(self.random_state)
            centroids, labels = kmeans2(X.astype(float), self.n_clusters, minit='points')
            self.cluster_centers_ = centroids
            return labels
            
        def predict(self, X):
            if hasattr(X, "values"):
                X = X.values
            distances = np.linalg.norm(X[:, np.newaxis] - self.cluster_centers_, axis=2)
            return np.argmin(distances, axis=1)
import joblib
import plotly.express as px
import plotly.graph_objects as go

MODEL_DIR = "models"
KMEANS_PATH = os.path.join(MODEL_DIR, "kmeans_rfm.joblib")
SCALER_PATH = os.path.join(MODEL_DIR, "scaler_rfm.joblib")
RFM_DATA_PATH = os.path.join("data", "processed", "rfm_data.csv")


def calculate_rfm(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate Recency, Frequency, and Monetary metrics for each customer."""
    df_clean = df.dropna(subset=['CustomerID']).copy()
    
    # Snapshot date for recency calculation (1 day after max date)
    snapshot_date = df_clean['InvoiceDate'].max() + pd.Timedelta(days=1)
    
    rfm = df_clean.groupby('CustomerID').agg({
        'InvoiceDate': lambda x: (snapshot_date - x.max()).days,  # Recency
        'InvoiceNo': 'nunique',                                  # Frequency
        'TotalPrice': 'sum'                                      # Monetary
    }).reset_index()
    
    rfm.columns = ['CustomerID', 'Recency', 'Frequency', 'Monetary']
    
    # Clean any non-positive monetary values if any
    rfm = rfm[rfm['Monetary'] > 0].reset_index(drop=True)
    return rfm


def train_customer_segmentation(df: pd.DataFrame, n_clusters: int = 4) -> pd.DataFrame:
    """
    Train KMeans model on normalized RFM values.
    Map clusters automatically to customer segments:
    VIP Customers, Loyal Customers, Regular Customers, At Risk Customers.
    Save trained model and scaler.
    """
    rfm = calculate_rfm(df)
    
    # Handle skewed distribution with log transformation + scaling
    rfm_log = np.log1p(rfm[['Recency', 'Frequency', 'Monetary']])
    
    scaler = StandardScaler()
    rfm_scaled = scaler.fit_transform(rfm_log)
    
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    rfm['Cluster'] = kmeans.fit_predict(rfm_scaled)
    
    # Calculate average RFM per cluster to map human-readable labels
    cluster_means = rfm.groupby('Cluster').agg({
        'Recency': 'mean',
        'Frequency': 'mean',
        'Monetary': 'mean'
    })
    
    # Score clusters based on high Monetary + Frequency, low Recency
    # Score = Monetary_mean + Frequency_mean - Recency_mean (normalized)
    scores = (
        (cluster_means['Monetary'] / cluster_means['Monetary'].max()) +
        (cluster_means['Frequency'] / cluster_means['Frequency'].max()) -
        (cluster_means['Recency'] / cluster_means['Recency'].max())
    )
    
    sorted_clusters = scores.sort_values(ascending=False).index.tolist()
    
    label_map = {}
    segment_names = ["VIP Customers", "Loyal Customers", "Regular Customers", "At Risk Customers"]
    for i, cluster_id in enumerate(sorted_clusters):
        label_map[cluster_id] = segment_names[min(i, len(segment_names)-1)]
        
    rfm['Segment'] = rfm['Cluster'].map(label_map)
    
    # Save models
    os.makedirs(MODEL_DIR, exist_ok=True)
    joblib.dump(kmeans, KMEANS_PATH)
    joblib.dump(scaler, SCALER_PATH)
    
    # Save RFM processed data
    os.makedirs(os.path.dirname(RFM_DATA_PATH), exist_ok=True)
    rfm.to_csv(RFM_DATA_PATH, index=False)
    
    return rfm


def load_rfm_data(df: pd.DataFrame = None) -> pd.DataFrame:
    """Load cached RFM data or compute and save if not found."""
    if os.path.exists(RFM_DATA_PATH):
        return pd.read_csv(RFM_DATA_PATH)
    elif df is not None:
        return train_customer_segmentation(df)
    else:
        raise ValueError("RFM data file missing and no DataFrame supplied.")


def fig_rfm_3d_scatter(rfm_df: pd.DataFrame):
    """3D Interactive Scatter Plot of RFM Segments."""
    fig = px.scatter_3d(
        rfm_df, x='Recency', y='Frequency', z='Monetary',
        color='Segment', hover_name='CustomerID',
        title="👥 3D Customer Segmentation (RFM Clusters)",
        labels={'Recency': 'Recency (Days)', 'Frequency': 'Frequency (Orders)', 'Monetary': 'Monetary (£)'},
        color_discrete_map={
            "VIP Customers": "#10B981",
            "Loyal Customers": "#3B82F6",
            "Regular Customers": "#F59E0B",
            "At Risk Customers": "#EF4444"
        },
        opacity=0.8
    )
    fig.update_layout(template="plotly_dark", height=550, margin=dict(l=10, r=10, t=50, b=10))
    return fig


def fig_segment_distribution(rfm_df: pd.DataFrame):
    """Pie chart of Customer Segments."""
    seg_counts = rfm_df['Segment'].value_counts().reset_index()
    seg_counts.columns = ['Segment', 'Count']
    
    fig = px.pie(
        seg_counts, names='Segment', values='Count',
        title="📊 Customer Segment Breakdown",
        hole=0.4,
        color='Segment',
        color_discrete_map={
            "VIP Customers": "#10B981",
            "Loyal Customers": "#3B82F6",
            "Regular Customers": "#F59E0B",
            "At Risk Customers": "#EF4444"
        }
    )
    fig.update_layout(template="plotly_dark", height=400, margin=dict(l=20, r=20, t=50, b=20))
    return fig


def fig_segment_revenue(rfm_df: pd.DataFrame):
    """Total Monetary Revenue by Customer Segment."""
    seg_rev = rfm_df.groupby('Segment')['Monetary'].sum().reset_index()
    
    fig = px.bar(
        seg_rev, x='Segment', y='Monetary',
        title="💰 Revenue Contribution by Customer Segment",
        labels={'Monetary': 'Total Revenue (£)', 'Segment': 'Customer Segment'},
        color='Segment',
        color_discrete_map={
            "VIP Customers": "#10B981",
            "Loyal Customers": "#3B82F6",
            "Regular Customers": "#F59E0B",
            "At Risk Customers": "#EF4444"
        }
    )
    fig.update_layout(template="plotly_dark", height=400, margin=dict(l=20, r=20, t=50, b=20))
    return fig
