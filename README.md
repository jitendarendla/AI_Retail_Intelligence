# 🛍️ AI Retail Intelligence Platform
> **Sales Analytics, Customer Segmentation, Market Basket Analysis, Product Recommendation, Sales Prediction, and AI Assistant**

An end-to-end, production-ready AI/ML Web Platform built using **Python, Streamlit, Scikit-Learn, FP-Growth (Mlxtend), Plotly, FAISS, Sentence Transformers, and Transformers (Flan-T5)**.

---

## 📌 Project Architecture & Directory Structure

```
AI-Retail-Intelligence-Platform/
│
├── data/
│   ├── raw/
│   │   └── Online Retail.xlsx
│   └── processed/
│       ├── cleaned_retail_data.csv
│       ├── rfm_data.csv
│       ├── daily_sales.csv
│       └── association_rules.csv
│
├── notebooks/
│   └── EDA_and_Modeling.ipynb
│
├── models/
│   ├── kmeans_rfm.joblib
│   ├── scaler_rfm.joblib
│   └── sales_forecast_rf.joblib
│
├── dashboard/
│   ├── app.py
│   └── pages/
│       ├── 1_🏠_Dashboard.py
│       ├── 2_📈_Sales_Analytics.py
│       ├── 3_👥_Customer_Segmentation.py
│       ├── 4_🛒_Market_Basket_Analysis.py
│       ├── 5_🤖_Product_Recommendation.py
│       ├── 6_📊_Sales_Prediction.py
│       ├── 7_💬_AI_Assistant.py
│       └── 8_📄_Reports.py
│
├── reports/
│   ├── retail_analytics_summary.csv
│   ├── customer_segments_rfm.csv
│   └── top_20_association_rules.csv
│
├── utils/
│   ├── __init__.py
│   ├── data_loader.py
│   ├── eda_analytics.py
│   ├── segmentation.py
│   ├── market_basket.py
│   ├── sales_prediction.py
│   └── rag_assistant.py
│
├── vector_db/
│   ├── faiss_index.bin
│   └── product_metadata.pkl
│
├── run_pipeline.py
├── requirements.txt
└── README.md
```

---

## 🎯 Key Modules & Features

### 1. Data Understanding & Cleaning (`utils/data_loader.py`)
- Automatic validation of dataset shape, missing values, duplicates, unique metrics.
- Data cleaning pipeline: Filter `Quantity > 0`, `UnitPrice > 0`, drop missing `CustomerID`, remove cancelled orders (`InvoiceNo` starting with 'C').
- Feature engineering: `TotalPrice = Quantity × UnitPrice`, `Year`, `Month`, `Day`, `Weekday`, `Hour`.

### 2. Exploratory Data Analysis (`utils/eda_analytics.py`)
- Interactive Plotly visualizations for temporal trends, top products/customers, country contributions, order volume, and revenue distributions.
- Executive KPI dashboard cards (Total Revenue, Orders, Customers, Unique Products, Avg Order Value).

### 3. Customer Segmentation (`utils/segmentation.py`)
- **RFM Analysis**: Recency, Frequency, Monetary calculation per customer.
- **KMeans Clustering**: Log-transform & standard scaling with cluster mapping to **VIP Customers**, **Loyal Customers**, **Regular Customers**, and **At-Risk Customers**.
- Interactive 3D RFM scatter plot and segment breakdown charts.

### 4. Market Basket Analysis & Product Recommendations (`utils/market_basket.py`)
- Transaction item matrix construction & **FP-Growth / Apriori Algorithm**.
- Calculation of **Support, Confidence, and Lift** metrics.
- Real-time Product Recommendation Engine: Input product name -> output Top 5 co-purchased recommendations with fallback bestsellers.

### 5. Sales Prediction (`utils/sales_prediction.py`)
- Daily sales aggregation with calendar, lag (`lag_1`, `lag_7`, `lag_14`, `lag_30`), and rolling average features.
- Supervised ML using **Random Forest Regressor** evaluated on MAE, RMSE, and R² Score.
- Interactive N-day future sales forecasting.

### 6. RAG AI Assistant (`utils/rag_assistant.py`)
- Domain-specific Knowledge Base built from transaction analytics and association rules.
- Vector search powered by **FAISS** vector store and `SentenceTransformer('all-MiniLM-L6-v2')`.
- Natural Language Question Answering using context retrieval & **HuggingFace Flan-T5**.

### 7. Interactive Streamlit Dashboard (`dashboard/app.py`)
- Custom Modern Dark Theme UI with glassmorphism cards and glow borders.
- Responsive sidebar navigation & persistent Date / Country filters.
- Integrated report downloads (CSV/Excel).

---

## 🚀 Quick Start & Installation

### 1. Clone & Install Dependencies
```bash
cd AI-Retail-Intelligence-Platform
pip install -r requirements.txt
```

### 2. Run Data & Model Pipeline
Executes raw dataset cleaning, trains ML models, mines market basket rules, and builds the FAISS vector database:
```bash
python run_pipeline.py
```

### 3. Launch Streamlit Web Application
```bash
streamlit run dashboard/app.py
```

---

## 📊 Summary of Machine Learning Models & Metrics

| Module | Algorithm / Technique | Key Output / Metric |
|---|---|---|
| Customer Segmentation | KMeans Clustering (k=4) | VIP, Loyal, Regular, At Risk Segments |
| Market Basket Analysis | FP-Growth / Apriori | Top Association Rules by Lift (> 2.0) |
| Sales Forecasting | Random Forest Regressor | MAE, RMSE, R² Score Evaluation |
| AI Assistant | Sentence Transformers + FAISS + Flan-T5 | Natural Language Semantic QA |

---

## 🎓 Final Year Major Project Highlights
- **Production Architecture**: Decoupled utilities (`utils/`), cached pipeline models (`models/`), and modular UI.
- **Enterprise-Ready Reports**: Instant CSV/Excel data exports for business stakeholders.
- **Modern UI/UX**: Dark mode layout, Plotly animations, loading spinners, and error handling.
