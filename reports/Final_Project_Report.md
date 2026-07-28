# 🎓 FINAL PROJECT REPORT
# AI Retail Intelligence Platform: Sales Analytics, Customer Segmentation, Market Basket Analysis, Product Recommendation, Sales Prediction, and AI Assistant

---

## 📌 PROJECT METADATA
- **Project Title:** AI Retail Intelligence Platform
- **Domain:** Data Science, Machine Learning, E-Commerce Analytics, Retrieval-Augmented Generation (RAG)
- **Dataset:** UCI Online Retail Dataset (`Online Retail.xlsx`, 541,909 records)
- **Technology Stack:** Python, Pandas, NumPy, Scikit-Learn, FP-Growth (Mlxtend), Plotly, Streamlit, FAISS, Sentence-Transformers, HuggingFace Transformers (Flan-T5)

---

## 1. ABSTRACT
In modern e-commerce enterprises, extracting actionable business insights from raw transactional data is critical for retaining customers, maximizing average basket values, and accurately forecasting inventory requirements. This project presents an end-to-end, production-grade **AI Retail Intelligence Platform** trained on 541,909 raw transactions from the Online Retail dataset. 

The platform integrates eight core machine learning and analytical modules:
1. **Data Understanding & Hygiene:** Preprocessing ~541k records down to 392,692 cleaned transaction line-items generating £8,887,208.89 in total revenue across 4,338 unique customers and 3,665 SKUs.
2. **Exploratory Data Analysis (EDA):** Interactive Plotly metrics analyzing temporal dynamics, top revenue products, high-spend customers, and geographic distributions.
3. **Customer Segmentation (RFM + KMeans):** Clustering customer accounts into four distinct behavioral personas: **VIP Customers**, **Loyal Customers**, **Regular Customers**, and **At Risk Customers**.
4. **Market Basket Mining (FP-Growth):** Mining 1,030 strong association rules based on Support, Confidence, and Lift metrics.
5. **Product Recommendation Engine:** Real-time cross-selling recommender delivering top co-purchased SKUs with bestseller fallback handling.
6. **Predictive Sales Forecasting:** Supervised Random Forest Regressor trained on lag and rolling features, achieving an R² accuracy score of 0.3280 and MAE of £11,779.68 on daily sales.
7. **RAG Business AI Assistant:** Contextual QA chatbot powered by FAISS vector store indexing and Sentence Transformers embeddings (`all-MiniLM-L6-v2`).
8. **Interactive Streamlit Web Dashboard:** Modern glassmorphic multi-tab user interface with dynamic date/country filtering and instant CSV exportable reporting.

---

## 2. PROBLEM STATEMENT & OBJECTIVES
Traditional retail analytics tools often operate in silos—offering static dashboards without predictive capabilities or intelligent natural language querying. Retail managers struggle to answer critical questions such as:
- *Which customer segments generate the majority of recurring revenue, and who is at risk of churning?*
- *What products are frequently purchased together, and how can cross-selling recommendations be automated?*
- *What is the forecasted daily sales trend for inventory planning?*
- *How can non-technical stakeholders instantly query business data in plain natural language?*

### Key Objectives:
- Clean and normalize raw e-commerce transaction logs.
- Segment customer bases using mathematical RFM scoring and unsupervised KMeans clustering.
- Automate market basket association mining using FP-Growth algorithms.
- Build a daily sales revenue forecaster using Random Forest regression.
- Implement a Retrieval-Augmented Generation (RAG) assistant using FAISS vector databases.
- Deploy an executive-level interactive web dashboard using Streamlit.

---

## 3. SYSTEM ARCHITECTURE & DATA FLOW
The system is built on a modular, decoupled architecture where data loading, feature engineering, machine learning pipelines, vector database indexing, and dashboard rendering are isolated into clean Python utility modules (`utils/`).

```
                              ┌────────────────────────┐
                              │  Online Retail.xlsx    │
                              └───────────┬────────────┘
                                          │
                                          ▼
                              ┌────────────────────────┐
                              │  utils/data_loader.py  │
                              └───────────┬────────────┘
                                          │
                    ┌─────────────────────┼─────────────────────┐
                    ▼                     ▼                     ▼
          ┌───────────────────┐ ┌───────────────────┐ ┌───────────────────┐
          │utils/segmentation │ │utils/market_basket│ │utils/sales_predict│
          │   (RFM + KMeans)  │ │ (FP-Growth Rules) │ │ (Random Forest)   │
          └─────────┬─────────┘ └─────────┬─────────┘ └─────────┬─────────┘
                    │                     │                     │
                    ▼                     ▼                     ▼
          ┌───────────────────┐ ┌───────────────────┐ ┌───────────────────┐
          │kmeans_rfm.joblib  │ │association_rules. │ │sales_forecast_rf. │
          │                   │ │       csv         │ │      joblib       │
          └─────────┬─────────┘ └─────────┬─────────┘ └─────────┬─────────┘
                    │                     │                     │
                    └─────────────────────┼─────────────────────┘
                                          │
                                          ▼
                              ┌────────────────────────┐
                              │ utils/rag_assistant.py │
                              │ (Sentence-Transformers │
                              │    + FAISS Vector DB)  │
                              └───────────┬────────────┘
                                          │
                                          ▼
                              ┌────────────────────────┐
                              │   dashboard/app.py     │
                              │ (Streamlit Executive UI│
                              └────────────────────────┘
```

---

## 4. MODULE BREAKDOWN & METHODOLOGY

### 4.1 Module 1 & 2: Data Understanding & Cleaning
- **Raw Transaction Processing:** Filters cancellations (`InvoiceNo` starting with 'C'), negative or zero `Quantity` and `UnitPrice`, and missing `CustomerID` values.
- **Feature Engineering:**
  $$\text{TotalPrice} = \text{Quantity} \times \text{UnitPrice}$$
  Temporal dimensions extracted: `Year`, `Month`, `Day`, `Weekday`, `Hour`.

### 4.2 Module 3: Exploratory Data Analysis (EDA)
- **Top Product Analysis:** Single highest revenue item identified as `PAPER CRAFT , LITTLE BIRDIE` (£168,469.60), followed by `REGENCY CAKESTAND 3 TIER` (£142,264.75).
- **Geographic Concentration:** United Kingdom accounts for >84% of total sales volume, followed by Germany, France, and EIRE.

### 4.3 Module 4: Customer Segmentation (RFM + KMeans)
- **Recency ($R$):** Days elapsed since customer's last purchase relative to snapshot date.
- **Frequency ($F$):** Total unique orders placed.
- **Monetary ($M$):** Cumulative spending (£).
- **Normalization & Clustering:** Features transformed via $\log(1+x)$ and standard scaling ($\mu=0, \sigma=1$). Unsupervised KMeans ($k=4$) assigns accounts to four segments:
  1. **VIP Customers (713):** High frequency, massive spend, recent activity.
  2. **Loyal Customers (837):** Steady repeat buyers with consistent order patterns.
  3. **Regular Customers (1,166):** Moderate spend and frequency.
  4. **At Risk Customers (1,622):** High recency (long inactivity window).

### 4.4 Module 5 & 6: Market Basket Analysis & Product Recommender
- **Algorithm:** FP-Growth algorithm applied to binary transaction item matrix (min support = 0.01).
- **Evaluation Metrics:**
  $$\text{Support}(A \rightarrow B) = P(A \cap B)$$
  $$\text{Confidence}(A \rightarrow B) = \frac{P(A \cap B)}{P(A)}$$
  $$\text{Lift}(A \rightarrow B) = \frac{\text{Confidence}(A \rightarrow B)}{P(B)}$$
- **Result:** 1,030 association rules generated. Real-time recommendation engine returns Top 5 co-purchased items (e.g., inputting `WHITE HANGING HEART T-LIGHT HOLDER` recommends `RED HANGING HEART T-LIGHT HOLDER`).

### 4.5 Module 7: Predictive Sales Forecasting
- **Daily Aggregation:** Total daily revenue aggregated over 305 unique operating days.
- **Feature Matrix:** Calendar features (`DayOfWeek`, `Month`, `Day`, `Quarter`, `Is_Weekend`), Lag features (`lag_1`, `lag_7`, `lag_14`, `lag_30`), and Rolling Averages (`rolling_7`, `rolling_14`).
- **Model:** Random Forest Regressor ($100$ decision trees, max depth = $12$).
- **Performance:**
  - **MAE:** £11,779.68
  - **RMSE:** £21,785.21
  - **R² Score:** 0.3280

### 4.6 Module 8: RAG Business AI Assistant
- **Embedding Model:** `SentenceTransformer('all-MiniLM-L6-v2')` generating 384-dimensional dense vectors.
- **Vector Database:** `faiss.IndexFlatL2` indexing structured knowledge documents.
- **Query Processing:** User natural language prompts are vector-searched using $L2$ distance to retrieve context, passed into Flan-T5 / domain QA synthesizer for instant answers.

### 4.7 Module 9: Streamlit Web Dashboard
- Built with a modern glassmorphism dark theme (`#0B0F19` obsidian background), custom KPI metric cards, dynamic date/country filters, 3D RFM scatter plots, and instant CSV export buttons.

---

## 5. EXPERIMENTAL RESULTS & METRICS SUMMARY

| Metric / Parameter | Value / Result |
|---|---|
| **Raw Transaction Log Size** | 541,909 records |
| **Cleaned Line Items** | 392,692 line items |
| **Total Gross Revenue** | £8,887,208.89 |
| **Unique Customer Accounts** | 4,338 accounts |
| **Total Mined Association Rules** | 1,030 rules |
| **KMeans Cluster Distribution** | VIP: 713 \| Loyal: 837 \| Regular: 1,166 \| At Risk: 1,622 |
| **Random Forest Forecast MAE** | £11,779.68 |
| **Random Forest Forecast RMSE** | £21,785.21 |
| **Random Forest Forecast R²** | 0.3280 |
| **FAISS Embedding Model** | Sentence Transformers `all-MiniLM-L6-v2` (384-dim) |

---

## 6. CONCLUSION & FUTURE SCOPE
The **AI Retail Intelligence Platform** successfully bridges the gap between complex machine learning algorithms and real-world business decision-making. By combining statistical RFM segmentation, rule mining, predictive sales forecasting, and a natural language RAG chatbot into a unified Streamlit application, retail managers gain 360-degree visibility over operations.

### Future Scope:
- Integration of Deep Learning forecasting models (LSTM / Temporal Fusion Transformers).
- Real-time streaming integration via Apache Kafka or WebSocket APIs.
- Multi-currency localization and automated automated email marketing campaign triggers for At Risk customers.
