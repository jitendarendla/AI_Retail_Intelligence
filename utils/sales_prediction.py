import os
import pandas as pd
import numpy as np
try:
    from sklearn.ensemble import RandomForestRegressor
except Exception as e:
    print(f"Notice: sklearn RandomForestRegressor DLL policy notice ({e}). Using DecisionTree/Ridge fallback.")
    try:
        from sklearn.tree import DecisionTreeRegressor as RandomForestRegressor
    except Exception:
        from sklearn.linear_model import Ridge as RandomForestRegressor

try:
    from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
except Exception:
    def mean_absolute_error(y_true, y_pred):
        return float(np.mean(np.abs(np.array(y_true) - np.array(y_pred))))
    def mean_squared_error(y_true, y_pred):
        return float(np.mean((np.array(y_true) - np.array(y_pred))**2))
    def r2_score(y_true, y_pred):
        y_true, y_pred = np.array(y_true), np.array(y_pred)
        ss_res = np.sum((y_true - y_pred) ** 2)
        ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
        return float(1 - (ss_res / (ss_tot + 1e-8)))
import joblib
import plotly.express as px
import plotly.graph_objects as go

MODEL_DIR = "models"
MODEL_PATH = os.path.join(MODEL_DIR, "sales_forecast_rf.joblib")
DAILY_SALES_PATH = os.path.join("data", "processed", "daily_sales.csv")


def prepare_daily_sales(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate total revenue per day."""
    df_temp = df.copy()
    df_temp['Date'] = pd.to_datetime(df_temp['InvoiceDate']).dt.date
    daily = df_temp.groupby('Date')['TotalPrice'].sum().reset_index()
    daily['Date'] = pd.to_datetime(daily['Date'])
    daily = daily.sort_values('Date').reset_index(drop=True)
    
    # Fill any missing dates in range with 0
    full_range = pd.date_range(start=daily['Date'].min(), end=daily['Date'].max(), freq='D')
    daily = daily.set_index('Date').reindex(full_range, fill_value=0.0).reset_index()
    daily.columns = ['Date', 'TotalPrice']
    return daily


def create_sales_features(daily_df: pd.DataFrame) -> pd.DataFrame:
    """Create temporal, lag, and rolling features for machine learning."""
    df_feat = daily_df.copy()
    
    # Calendar features
    df_feat['DayOfWeek'] = df_feat['Date'].dt.dayofweek
    df_feat['Month'] = df_feat['Date'].dt.month
    df_feat['Day'] = df_feat['Date'].dt.day
    df_feat['Quarter'] = df_feat['Date'].dt.quarter
    df_feat['Is_Weekend'] = df_feat['DayOfWeek'].apply(lambda x: 1 if x >= 5 else 0)
    
    # Lag features
    df_feat['lag_1'] = df_feat['TotalPrice'].shift(1)
    df_feat['lag_7'] = df_feat['TotalPrice'].shift(7)
    df_feat['lag_14'] = df_feat['TotalPrice'].shift(14)
    df_feat['lag_30'] = df_feat['TotalPrice'].shift(30)
    
    # Rolling mean features
    df_feat['rolling_7'] = df_feat['TotalPrice'].shift(1).rolling(window=7).mean()
    df_feat['rolling_14'] = df_feat['TotalPrice'].shift(1).rolling(window=14).mean()
    
    # Drop NaNs caused by lags
    df_feat = df_feat.dropna().reset_index(drop=True)
    return df_feat


def train_sales_forecaster(df: pd.DataFrame) -> dict:
    """
    Train Random Forest Regressor on Daily Sales.
    Evaluate using MAE, RMSE, R² Score.
    Save model and return results dict.
    """
    daily = prepare_daily_sales(df)
    
    # Save daily sales to CSV
    os.makedirs(os.path.dirname(DAILY_SALES_PATH), exist_ok=True)
    daily.to_csv(DAILY_SALES_PATH, index=False)
    
    df_feat = create_sales_features(daily)
    
    feature_cols = ['DayOfWeek', 'Month', 'Day', 'Quarter', 'Is_Weekend', 
                    'lag_1', 'lag_7', 'lag_14', 'lag_30', 'rolling_7', 'rolling_14']
    
    X = df_feat[feature_cols]
    y = df_feat['TotalPrice']
    dates = df_feat['Date']
    
    # Time-based Train-Test Split (80% train, 20% test)
    split_idx = int(len(X) * 0.8)
    X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
    y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]
    dates_test = dates.iloc[split_idx:]
    
    rf = RandomForestRegressor(n_estimators=100, random_state=42, max_depth=12)
    rf.fit(X_train, y_train)
    
    preds = rf.predict(X_test)
    
    mae = float(mean_absolute_error(y_test, preds))
    rmse = float(np.sqrt(mean_squared_error(y_test, preds)))
    r2 = float(r2_score(y_test, preds))
    
    # Save model
    os.makedirs(MODEL_DIR, exist_ok=True)
    joblib.dump(rf, MODEL_PATH)
    
    eval_results = {
        "mae": mae,
        "rmse": rmse,
        "r2": r2,
        "dates_test": dates_test,
        "y_test": y_test,
        "preds": preds,
        "model": rf,
        "feature_cols": feature_cols
    }
    return eval_results


def forecast_future_sales(daily_df: pd.DataFrame, days_ahead: int = 14) -> pd.DataFrame:
    """Recursively forecast sales for N days into the future."""
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError("Trained sales forecasting model not found.")
    
    rf = joblib.load(MODEL_PATH)
    
    df_feat = create_sales_features(daily_df)
    last_known_date = daily_df['Date'].max()
    
    current_history = daily_df.copy()
    future_rows = []
    
    for i in range(1, days_ahead + 1):
        next_date = last_known_date + pd.Timedelta(days=i)
        
        # Calculate features on current_history
        dow = next_date.dayofweek
        month = next_date.month
        day = next_date.day
        quarter = next_date.quarter
        is_weekend = 1 if dow >= 5 else 0
        
        sales_series = current_history['TotalPrice']
        lag_1 = sales_series.iloc[-1]
        lag_7 = sales_series.iloc[-7] if len(sales_series) >= 7 else sales_series.mean()
        lag_14 = sales_series.iloc[-14] if len(sales_series) >= 14 else sales_series.mean()
        lag_30 = sales_series.iloc[-30] if len(sales_series) >= 30 else sales_series.mean()
        
        rolling_7 = sales_series.tail(7).mean()
        rolling_14 = sales_series.tail(14).mean()
        
        feature_cols = ['DayOfWeek', 'Month', 'Day', 'Quarter', 'Is_Weekend', 
                        'lag_1', 'lag_7', 'lag_14', 'lag_30', 'rolling_7', 'rolling_14']
        feat_df = pd.DataFrame([[dow, month, day, quarter, is_weekend,
                                 lag_1, lag_7, lag_14, lag_30, rolling_7, rolling_14]], columns=feature_cols)
        
        pred_val = max(0.0, float(rf.predict(feat_df)[0]))
        
        future_rows.append({"Date": next_date, "Predicted_Sales": pred_val, "Type": "Forecast"})
        
        # Append prediction to history for subsequent lag steps
        current_history = pd.concat([
            current_history, 
            pd.DataFrame([{"Date": next_date, "TotalPrice": pred_val}])
        ], ignore_index=True)
        
    return pd.DataFrame(future_rows)


def fig_actual_vs_predicted(eval_results: dict):
    """Plot Actual Sales vs Predicted Sales on test dataset."""
    df_plot = pd.DataFrame({
        'Date': eval_results['dates_test'],
        'Actual Sales': eval_results['y_test'],
        'Predicted Sales': eval_results['preds']
    })
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df_plot['Date'], y=df_plot['Actual Sales'], mode='lines+markers', name='Actual Sales', line=dict(color='#10B981', width=2)))
    fig.add_trace(go.Scatter(x=df_plot['Date'], y=df_plot['Predicted Sales'], mode='lines+markers', name='Predicted Sales', line=dict(color='#F59E0B', width=2, dash='dash')))
    
    fig.update_layout(
        title="📊 Sales Forecast: Actual vs Predicted Daily Sales (Test Dataset)",
        xaxis_title="Date", yaxis_title="Revenue (£)",
        template="plotly_dark", height=450, margin=dict(l=20, r=20, t=50, b=20)
    )
    return fig


def fig_future_forecast(daily_df: pd.DataFrame, future_df: pd.DataFrame):
    """Plot historical sales + future forecast."""
    recent_history = daily_df.tail(60).copy()
    recent_history['Type'] = 'Historical'
    recent_history.rename(columns={'TotalPrice': 'Sales'}, inplace=True)
    
    fut = future_df.copy()
    fut.rename(columns={'Predicted_Sales': 'Sales'}, inplace=True)
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=recent_history['Date'], y=recent_history['Sales'], mode='lines', name='Historical Sales', line=dict(color='#3B82F6', width=2)))
    fig.add_trace(go.Scatter(x=fut['Date'], y=fut['Sales'], mode='lines+markers', name='Future Forecast', line=dict(color='#EC4899', width=3)))
    
    fig.update_layout(
        title="🔮 Future Sales Forecast Projection",
        xaxis_title="Date", yaxis_title="Revenue (£)",
        template="plotly_dark", height=450, margin=dict(l=20, r=20, t=50, b=20)
    )
    return fig
