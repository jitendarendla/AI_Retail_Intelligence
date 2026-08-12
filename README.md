# 🛍️ AI Retail Intelligence Platform
> **Sales Analytics, Customer Segmentation, Market Basket Analysis, Product Recommendation, Sales Prediction, and RAG AI Assistant**

An end-to-end, production-ready AI/ML Web Platform built using **Python, Streamlit, Scikit-Learn, FP-Growth (Mlxtend), Plotly, FAISS, Sentence Transformers, and HuggingFace Transformers**.

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Streamlit App](https://img.shields.io/badge/Streamlit-1.30%2B-FF4B4B.svg)](https://streamlit.io/)
[![Machine Learning](https://img.shields.io/badge/ML-Scikit--Learn-F7931E.svg)](https://scikit-learn.org/)
[![GitHub Repo](https://img.shields.io/badge/GitHub-Repository-181717.svg)](https://github.com/jitendarendla/AI_Retail_Intelligence)

---

## 📌 Project Architecture & Directory Structure

```
AI_Retail_Intelligence/
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
│   ├── 01_Data_Understanding.ipynb
│   ├── 02_Data_Cleaning.ipynb
│   ├── 03_Exploratory_Data_Analysis.ipynb
│   ├── 04_Customer_Segmentation_RFM.ipynb
│   ├── 05_Market_Basket_Analysis.ipynb
│   ├── 06_Product_Recommendation_Engine.ipynb
│   ├── 07_Sales_Prediction_RandomForest.ipynb
│   ├── 08_AI_Assistant_RAG_FAISS.ipynb
│   ├── 09_Streamlit_Dashboard_Guide.ipynb
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
│   ├── PRESENTATION_PPT_GUIDE.md   <-- Full 15-Slide PPT Creation & Speaking Guide
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

### 1. Data Cleaning & Integrity Audit (`utils/data_loader.py`)
- Automatic validation of dataset shape, missing values, duplicates, unique metrics.
- Data cleaning pipeline: Filter `Quantity > 0`, `UnitPrice > 0`, drop missing `CustomerID`, remove cancelled orders (`InvoiceNo` starting with 'C').
- Standardized 541,909 raw lines into **392,692 clean, high-integrity records** generating **£8,887,208.89** across **4,338 customers**.

### 2. Exploratory Data Analysis (`utils/eda_analytics.py`)
- Interactive Plotly visualizations for temporal trends, top products/customers, country contributions, order volume, and revenue distributions.
- Executive KPI metrics: Total Revenue, Orders, Customers, Unique SKUs, Avg Order Value.

### 3. Customer RFM Segmentation (`utils/segmentation.py`)
- **RFM Analysis**: Recency ($R$), Frequency ($F$), Monetary ($M$) metrics per customer.
- **Log-Scaled KMeans Clustering**: Log transformation $\log(1+x)$ + `StandardScaler` to handle heavy-tailed monetary distributions.
- Maps customers into 4 target personas: **VIP Customers**, **Loyal Customers**, **Regular Customers**, and **At-Risk Customers**.

### 4. Market Basket Analysis & Product Recommendations (`utils/market_basket.py`)
- Binary transaction matrix construction & **FP-Growth Algorithm** (min support = 0.01).
- Mining **1,030 association rules** evaluated on Support, Confidence, and Lift.
- Real-time Product Recommendation Engine: Selected item $\rightarrow$ Top 5 co-purchased companion recommendations with bestseller fallback.

### 5. Sales Prediction (`utils/sales_prediction.py`)
- Daily sales aggregation across 305 operating days with calendar, lag (`lag_1`, `lag_7`, `lag_14`, `lag_30`), and rolling average features.
- Supervised ML using **Random Forest Regressor** evaluated on MAE (£11,779.68), RMSE (£21,785.21), and $R^2$ Score (0.3280).
- Interactive 1 to 60-day future sales forecasting.

### 6. RAG AI Assistant (`utils/rag_assistant.py`)
- Domain-specific Knowledge Base built from dataset analytics and association rules.
- Vector search powered by **FAISS** vector store and `SentenceTransformer('all-MiniLM-L6-v2')`.
- Natural Language Question Answering using context retrieval.

### 7. Glassmorphic Web App (`dashboard/app.py`)
- Custom Modern Dark Theme UI (`#0F172A`) with glassmorphism cards and glow borders.
- Responsive sidebar navigation, global Date/Country filters, and instant CSV downloads.

---

## 🚀 Quick Start & Installation

### 1. Clone & Install Dependencies
```bash
git clone https://github.com/jitendarendla/AI_Retail_Intelligence.git
cd AI_Retail_Intelligence
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

## 📽️ PowerPoint (PPT) Presentation & Defense Blueprint

For a complete slide-by-slide guide to building your presentation slides and word-for-word speaking scripts for your viva presentation, refer to:
👉 **[reports/PRESENTATION_PPT_GUIDE.md](file:///c:/Users/jiten/Desktop/AI/reports/PRESENTATION_PPT_GUIDE.md)**

### 15-Slide Presentation Structure Summary

```
Slide 1  : Title & Project Overview (Cover, Tech Stack, Repo Link)
Slide 2  : Executive Summary & Business Need (Challenges vs AI Solutions)
Slide 3  : System Architecture & Data Flow Diagram (Decoupled Pipeline)
Slide 4  : Dataset Preprocessing & Cleaning (541k -> 392k Clean Records)
Slide 5  : Exploratory Data Analysis (EDA Key Findings & Seasonality)
Slide 6  : Customer RFM Segmentation (Log-Scaled KMeans k=4 Personas)
Slide 7  : Market Basket Analysis (FP-Growth 1,030 Mined Rules & Lift Metrics)
Slide 8  : AI Product Recommender Engine (Cross-Selling & Bestseller Fallback)
Slide 9  : Daily Sales Prediction (Random Forest Autoregressive Model)
Slide 10 : RAG AI Business Assistant (Sentence Transformers + FAISS)
Slide 11 : Glassmorphic Web App (Streamlit Responsive UI & Filters)
Slide 12 : Experimental Benchmarks & Validation Metrics Table
Slide 13 : Step-by-Step Live Viva Demonstration Script
Slide 14 : Strategic Business Impact & Future Scope
Slide 15 : Examiner Viva Q&A Defense Cheatsheet (Top 12 Questions & Answers)
```

---

## 📊 Summary of Machine Learning Models & Metrics

| Module | Machine Learning Algorithm | Evaluation Metric / Benchmark Output | Status |
|---|---|---|:---:|
| **Customer Segmentation** | KMeans Clustering ($k=4$) | VIP (713), Loyal (837), Regular (1,166), At Risk (1,622) | ✅ Verified |
| **Market Basket Mining** | FP-Growth (min_support = 0.01) | 1,030 Association Rules (Max Lift: 18.53) | ✅ Verified |
| **Sales Forecasting** | Random Forest Regressor | MAE: £11,779.68 \| RMSE: £21,785.21 \| $R^2$: 0.3280 | ✅ Verified |
| **AI Assistant** | Sentence Transformers + FAISS | 384-Dim Vector Match Semantic QA | ✅ Verified |

---

## 🎓 Final Year Major Project Highlights
- **Production Architecture**: Decoupled utilities (`utils/`), cached pipeline models (`models/`), and modular Streamlit UI.
- **Enterprise-Ready Reports**: Instant CSV data exports for business stakeholders.
- **10 Executed Jupyter Notebooks**: Complete step-by-step code learning with saved outputs in `notebooks/`.
- **GitHub Repository**: [https://github.com/jitendarendla/AI_Retail_Intelligence](https://github.com/jitendarendla/AI_Retail_Intelligence.git)
