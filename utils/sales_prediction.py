import os
import pandas as pd
import numpy as np
import torch
import torch.nn as nn

try:
    from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
except Exception:
    def mean_absolute_error(y_true, y_pred):
        return float(np.mean(np.abs(np.array(y_true) - np.array(y_pred))))
    def mean_squared_error(y_true, y_pred):
        return float(np.mean((np.array(y_true) - np.array(y_pred)) ** 2))
    def r2_score(y_true, y_pred):
        y_true, y_pred = np.array(y_true), np.array(y_pred)
        ss_res = np.sum((y_true - y_pred) ** 2)
        ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
        return float(1 - (ss_res / (ss_tot + 1e-8)))

MODEL_DIR = "models"
LSTM_MODEL_PATH = os.path.join(MODEL_DIR, "sales_forecast_lstm.pt")
ANN_MODEL_PATH = os.path.join(MODEL_DIR, "sales_forecast_ann.pt")
DAILY_SALES_PATH = os.path.join("data", "processed", "daily_sales.csv")

# In-memory cache keyed by (num_days, total_revenue, model_type) to make slider horizon updates instant
_FORECAST_CACHE = {}


class SalesANN(nn.Module):
    """Multi-Layer Perceptron (Artificial Neural Network) for daily sales regression."""
    def __init__(self, input_dim: int):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, 32),
            nn.ReLU(),
            nn.Dropout(0.15),
            nn.Linear(32, 16),
            nn.ReLU(),
            nn.Linear(16, 1),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


class SalesLSTM(nn.Module):
    """Hybrid LSTM sequence network fused with target-day calendar context."""
    def __init__(self, seq_input_dim: int = 8, ctx_dim: int = 12):
        super().__init__()
        self.lstm = nn.LSTM(seq_input_dim, 16, num_layers=1, batch_first=True)
        self.head = nn.Sequential(
            nn.Linear(16 + ctx_dim, 24),
            nn.ReLU(),
            nn.Linear(24, 1),
        )

    def forward(self, seq_x: torch.Tensor, ctx_x: torch.Tensor) -> torch.Tensor:
        out, _ = self.lstm(seq_x)
        combined = torch.cat([out[:, -1, :], ctx_x], dim=1)
        return self.head(combined)


def prepare_daily_sales(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate total revenue per day."""
    df_temp = df.copy()
    df_temp["Date"] = pd.to_datetime(df_temp["InvoiceDate"]).dt.date
    daily = df_temp.groupby("Date")["TotalPrice"].sum().reset_index()
    daily["Date"] = pd.to_datetime(daily["Date"])
    daily = daily.sort_values("Date").reset_index(drop=True)

    full_range = pd.date_range(start=daily["Date"].min(), end=daily["Date"].max(), freq="D")
    daily = daily.set_index("Date").reindex(full_range, fill_value=0.0).reset_index()
    daily.columns = ["Date", "TotalPrice"]
    return daily


def _build_ann_features(daily_df: pd.DataFrame, max_lag: int) -> tuple[pd.DataFrame, list[str]]:
    df_feat = daily_df.copy()
    dow = df_feat["Date"].dt.dayofweek
    for d in range(7):
        df_feat[f"dow_{d}"] = (dow == d).astype(np.float32)
    df_feat["month_norm"] = (df_feat["Date"].dt.month / 12.0).astype(np.float32)

    lag_cols = []
    if max_lag >= 28:
        df_feat["lag_1"] = df_feat["TotalPrice"].shift(1)
        df_feat["lag_7"] = df_feat["TotalPrice"].shift(7)
        df_feat["lag_14"] = df_feat["TotalPrice"].shift(14)
        df_feat["lag_28"] = df_feat["TotalPrice"].shift(28)
        df_feat["rolling_7"] = df_feat["TotalPrice"].shift(1).rolling(7).mean()
        df_feat["rolling_14"] = df_feat["TotalPrice"].shift(1).rolling(14).mean()
        lag_cols = ["lag_1", "lag_7", "lag_14", "lag_28", "rolling_7", "rolling_14"]
    elif max_lag >= 7:
        df_feat["lag_1"] = df_feat["TotalPrice"].shift(1)
        df_feat["lag_7"] = df_feat["TotalPrice"].shift(7)
        df_feat["rolling_7"] = df_feat["TotalPrice"].shift(1).rolling(7).mean()
        lag_cols = ["lag_1", "lag_7", "rolling_7"]
    else:
        df_feat["lag_1"] = df_feat["TotalPrice"].shift(1)
        lag_cols = ["lag_1"]

    df_feat = df_feat.dropna().reset_index(drop=True)
    feature_cols = [f"dow_{d}" for d in range(7)] + ["month_norm"] + lag_cols
    return df_feat, feature_cols


def _train_ann(daily: pd.DataFrame) -> dict:
    n_days = len(daily)
    max_lag = 28 if n_days >= 45 else (7 if n_days >= 15 else 1)
    df_feat, feature_cols = _build_ann_features(daily, max_lag=max_lag)

    X = df_feat[feature_cols].values.astype(np.float32)
    y = df_feat["TotalPrice"].values.astype(np.float32).reshape(-1, 1)
    dates = df_feat["Date"]

    split_idx = max(1, min(len(X) - 1, int(len(X) * 0.8)))
    X_mean = X[:split_idx].mean(axis=0)
    X_std = X[:split_idx].std(axis=0) + 1e-6
    y_mean = float(y[:split_idx].mean())
    y_std = float(y[:split_idx].std() + 1e-6)

    X_tr = torch.tensor((X[:split_idx] - X_mean) / X_std, dtype=torch.float32)
    X_te = torch.tensor((X[split_idx:] - X_mean) / X_std, dtype=torch.float32)
    y_tr = torch.tensor((y[:split_idx] - y_mean) / y_std, dtype=torch.float32)
    y_actual = y[split_idx:].flatten()

    torch.manual_seed(42)
    np.random.seed(42)
    model = SalesANN(input_dim=len(feature_cols))
    optimizer = torch.optim.Adam(model.parameters(), lr=0.005, weight_decay=0.02)
    loss_fn = nn.HuberLoss()

    model.train()
    for _ in range(180):
        optimizer.zero_grad()
        loss = loss_fn(model(X_tr), y_tr)
        loss.backward()
        optimizer.step()

    model.eval()
    with torch.no_grad():
        preds = np.clip(model(X_te).numpy().flatten() * y_std + y_mean, 0.0, None)

    mae = float(mean_absolute_error(y_actual, preds))
    rmse = float(np.sqrt(mean_squared_error(y_actual, preds)))
    r2 = float(r2_score(y_actual, preds))

    os.makedirs(MODEL_DIR, exist_ok=True)
    torch.save({
        "model_state": model.state_dict(),
        "X_mean": X_mean,
        "X_std": X_std,
        "y_mean": y_mean,
        "y_std": y_std,
        "feature_cols": feature_cols,
        "max_lag": max_lag,
    }, ANN_MODEL_PATH)

    return {
        "model_type": "ann",
        "model_label": "ANN (Multi-Layer Perceptron)",
        "mae": mae,
        "rmse": rmse,
        "r2": r2,
        "dates_test": dates.iloc[split_idx:],
        "y_test": y_actual,
        "preds": preds,
        "bundle": {
            "model": model,
            "X_mean": X_mean,
            "X_std": X_std,
            "y_mean": y_mean,
            "y_std": y_std,
            "feature_cols": feature_cols,
            "max_lag": max_lag,
        },
    }


def _train_lstm(daily: pd.DataFrame) -> dict:
    y_raw = daily["TotalPrice"].values.astype(np.float32)
    dow_all = daily["Date"].dt.dayofweek.values
    dow_oh = np.eye(7, dtype=np.float32)[dow_all]
    m_feat = (daily["Date"].dt.month.values / 12.0).astype(np.float32).reshape(-1, 1)

    seq_len = 14 if len(daily) >= 35 else max(3, min(7, len(daily) // 3))
    sp_raw = max(seq_len + 1, int(len(y_raw) * 0.8))
    y_mean = float(y_raw[:sp_raw].mean())
    y_std = float(y_raw[:sp_raw].std() + 1e-6)
    y_sc = (y_raw - y_mean) / y_std

    Xs, Xc, ys_list, target_dates = [], [], [], []
    for i in range(seq_len, len(y_sc)):
        seq_mat = np.column_stack([y_sc[i - seq_len:i].reshape(-1, 1), dow_oh[i - seq_len:i]])
        lag_7 = y_sc[i - 7] if i >= 7 else y_sc[i - 1]
        lag_14 = y_sc[i - 14] if i >= 14 else y_sc[i - seq_len:i].mean()
        ctx_vec = np.concatenate([
            dow_oh[i],
            m_feat[i],
            [y_sc[i - 1], lag_7, lag_14, y_sc[i - seq_len:i].mean()],
        ])
        Xs.append(seq_mat)
        Xc.append(ctx_vec)
        ys_list.append(y_sc[i])
        target_dates.append(daily["Date"].iloc[i])

    Xs_arr = np.array(Xs, dtype=np.float32)
    Xc_arr = np.array(Xc, dtype=np.float32)
    ys_arr = np.array(ys_list, dtype=np.float32).reshape(-1, 1)

    split_idx = max(1, min(len(Xs_arr) - 1, int(len(Xs_arr) * 0.8)))
    X_tr_s = torch.tensor(Xs_arr[:split_idx], dtype=torch.float32)
    X_tr_c = torch.tensor(Xc_arr[:split_idx], dtype=torch.float32)
    y_tr = torch.tensor(ys_arr[:split_idx], dtype=torch.float32)

    X_te_s = torch.tensor(Xs_arr[split_idx:], dtype=torch.float32)
    X_te_c = torch.tensor(Xc_arr[split_idx:], dtype=torch.float32)
    y_actual = ys_arr[split_idx:].flatten() * y_std + y_mean

    torch.manual_seed(42)
    np.random.seed(42)
    model = SalesLSTM(seq_input_dim=8, ctx_dim=12)
    optimizer = torch.optim.Adam(model.parameters(), lr=0.005, weight_decay=0.05)
    loss_fn = nn.MSELoss()

    model.train()
    for _ in range(180):
        optimizer.zero_grad()
        loss = loss_fn(model(X_tr_s, X_tr_c), y_tr)
        loss.backward()
        optimizer.step()

    model.eval()
    with torch.no_grad():
        preds = np.clip(model(X_te_s, X_te_c).numpy().flatten() * y_std + y_mean, 0.0, None)

    mae = float(mean_absolute_error(y_actual, preds))
    rmse = float(np.sqrt(mean_squared_error(y_actual, preds)))
    r2 = float(r2_score(y_actual, preds))

    os.makedirs(MODEL_DIR, exist_ok=True)
    torch.save({
        "model_state": model.state_dict(),
        "y_mean": y_mean,
        "y_std": y_std,
        "seq_len": seq_len,
    }, LSTM_MODEL_PATH)

    return {
        "model_type": "lstm",
        "model_label": "LSTM (Recurrent Neural Network)",
        "mae": mae,
        "rmse": rmse,
        "r2": r2,
        "dates_test": pd.Series(target_dates[split_idx:]),
        "y_test": y_actual,
        "preds": preds,
        "bundle": {
            "model": model,
            "y_mean": y_mean,
            "y_std": y_std,
            "seq_len": seq_len,
        },
    }


def train_sales_forecaster(df: pd.DataFrame, model_type: str = "lstm") -> dict:
    """
    Train LSTM or ANN PyTorch neural network on daily sales.
    Evaluate using MAE, RMSE, R² Score and cache trained weights.
    """
    model_key = (model_type or "lstm").strip().lower()
    if model_key not in ("lstm", "ann"):
        model_key = "lstm"

    daily = prepare_daily_sales(df)
    os.makedirs(os.path.dirname(DAILY_SALES_PATH), exist_ok=True)
    daily.to_csv(DAILY_SALES_PATH, index=False)

    cache_sig = (len(daily), round(float(daily["TotalPrice"].sum()), 2), model_key)
    if cache_sig in _FORECAST_CACHE:
        return _FORECAST_CACHE[cache_sig]

    if len(daily) < 8:
        avg_val = float(daily["TotalPrice"].mean()) if not daily.empty else 0.0
        res = {
            "model_type": model_key,
            "model_label": "LSTM (Recurrent Neural Network)" if model_key == "lstm" else "ANN (Multi-Layer Perceptron)",
            "mae": 0.0,
            "rmse": 0.0,
            "r2": 0.0,
            "dates_test": daily["Date"],
            "y_test": daily["TotalPrice"].values,
            "preds": np.full(len(daily), avg_val),
            "bundle": None,
        }
        _FORECAST_CACHE[cache_sig] = res
        return res

    res = _train_ann(daily) if model_key == "ann" else _train_lstm(daily)
    _FORECAST_CACHE[cache_sig] = res
    return res


def forecast_future_sales(daily_df: pd.DataFrame, days_ahead: int = 14, model_type: str = "lstm") -> pd.DataFrame:
    """Recursively forecast sales for N days into the future using trained LSTM or ANN."""
    model_key = (model_type or "lstm").strip().lower()
    if model_key not in ("lstm", "ann"):
        model_key = "lstm"

    daily = daily_df.copy()
    daily["Date"] = pd.to_datetime(daily["Date"])
    daily = daily.sort_values("Date").reset_index(drop=True)

    cache_sig = (len(daily), round(float(daily["TotalPrice"].sum()), 2), model_key)
    cached = _FORECAST_CACHE.get(cache_sig)
    bundle = cached.get("bundle") if cached else None

    if bundle is None:
        if model_key == "ann" and os.path.exists(ANN_MODEL_PATH):
            ckpt = torch.load(ANN_MODEL_PATH, weights_only=False)
            m = SalesANN(input_dim=len(ckpt["feature_cols"]))
            m.load_state_dict(ckpt["model_state"])
            m.eval()
            bundle = {**ckpt, "model": m}
        elif model_key == "lstm" and os.path.exists(LSTM_MODEL_PATH):
            ckpt = torch.load(LSTM_MODEL_PATH, weights_only=False)
            m = SalesLSTM()
            m.load_state_dict(ckpt["model_state"])
            m.eval()
            bundle = {**ckpt, "model": m}

    last_known_date = daily["Date"].max()
    future_rows = []

    if bundle is None:
        avg_val = max(0.0, float(daily["TotalPrice"].mean()))
        for i in range(1, days_ahead + 1):
            next_date = last_known_date + pd.Timedelta(days=i)
            future_rows.append({"Date": next_date, "Predicted_Sales": avg_val, "Type": "Forecast"})
        return pd.DataFrame(future_rows)

    model = bundle["model"]
    model.eval()

    if model_key == "ann":
        X_mean = bundle["X_mean"]
        X_std = bundle["X_std"]
        y_mean = bundle["y_mean"]
        y_std = bundle["y_std"]
        max_lag = bundle["max_lag"]

        sales_hist = list(daily["TotalPrice"].astype(float).values)
        for i in range(1, days_ahead + 1):
            next_date = last_known_date + pd.Timedelta(days=i)
            dow = next_date.dayofweek
            dow_vec = [1.0 if d == dow else 0.0 for d in range(7)]
            month_norm = [next_date.month / 12.0]

            s = pd.Series(sales_hist)
            lag_1 = float(s.iloc[-1])
            if max_lag >= 28:
                lag_7 = float(s.iloc[-7]) if len(s) >= 7 else float(s.mean())
                lag_14 = float(s.iloc[-14]) if len(s) >= 14 else float(s.mean())
                lag_28 = float(s.iloc[-28]) if len(s) >= 28 else float(s.mean())
                roll_7 = float(s.tail(7).mean())
                roll_14 = float(s.tail(14).mean())
                lag_vals = [lag_1, lag_7, lag_14, lag_28, roll_7, roll_14]
            elif max_lag >= 7:
                lag_7 = float(s.iloc[-7]) if len(s) >= 7 else float(s.mean())
                roll_7 = float(s.tail(7).mean())
                lag_vals = [lag_1, lag_7, roll_7]
            else:
                lag_vals = [lag_1]

            raw_vec = np.array(dow_vec + month_norm + lag_vals, dtype=np.float32)
            norm_vec = torch.tensor(((raw_vec - X_mean) / X_std).reshape(1, -1), dtype=torch.float32)
            with torch.no_grad():
                pred_val = max(0.0, float(model(norm_vec).item() * y_std + y_mean))

            future_rows.append({"Date": next_date, "Predicted_Sales": pred_val, "Type": "Forecast"})
            sales_hist.append(pred_val)
    else:
        y_mean = bundle["y_mean"]
        y_std = bundle["y_std"]
        seq_len = bundle["seq_len"]

        sales_sc = list(((daily["TotalPrice"].astype(np.float32).values - y_mean) / y_std))
        dow_hist = list(daily["Date"].dt.dayofweek.values)

        for i in range(1, days_ahead + 1):
            next_date = last_known_date + pd.Timedelta(days=i)
            dow = next_date.dayofweek
            dow_oh_target = np.eye(7, dtype=np.float32)[dow]
            month_norm = np.array([next_date.month / 12.0], dtype=np.float32)

            win_sales = np.array(sales_sc[-seq_len:], dtype=np.float32).reshape(-1, 1)
            win_dows = np.eye(7, dtype=np.float32)[dow_hist[-seq_len:]]
            seq_mat = np.column_stack([win_sales, win_dows]).reshape(1, seq_len, 8)

            lag_1 = sales_sc[-1]
            lag_7 = sales_sc[-7] if len(sales_sc) >= 7 else lag_1
            lag_14 = sales_sc[-14] if len(sales_sc) >= 14 else float(np.mean(sales_sc[-seq_len:]))
            ctx_vec = np.concatenate([
                dow_oh_target,
                month_norm,
                np.array([lag_1, lag_7, lag_14, float(np.mean(sales_sc[-seq_len:]))], dtype=np.float32),
            ]).reshape(1, -1)

            with torch.no_grad():
                pred_sc = float(model(torch.tensor(seq_mat), torch.tensor(ctx_vec)).item())
            pred_val = max(0.0, pred_sc * y_std + y_mean)
            pred_sc_clamped = (pred_val - y_mean) / y_std

            future_rows.append({"Date": next_date, "Predicted_Sales": pred_val, "Type": "Forecast"})
            sales_sc.append(pred_sc_clamped)
            dow_hist.append(dow)

    return pd.DataFrame(future_rows)
