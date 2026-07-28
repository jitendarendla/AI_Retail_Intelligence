# 📊 MAJOR PROJECT PRESENTATION SLIDE DECK
# Title: AI Retail Intelligence Platform

---

### 🟢 SLIDE 1: Title Slide
- **Title:** AI Retail Intelligence Platform
- **Subtitle:** Sales Analytics, Customer Segmentation, Market Basket Analysis, Product Recommendation, Sales Prediction & AI Assistant
- **Dataset:** UCI Online Retail Dataset (~541k records)
- **Domain:** Data Science, Machine Learning, AI & Web Application Development

---

### 🟢 SLIDE 2: Executive Summary & Project Vision
- **Objective:** Build an end-to-end operational AI platform combining ML analytics, market basket mining, predictive sales forecasting, and a RAG AI assistant into a responsive Streamlit dashboard.
- **Key Achievements:**
  - Cleaned 541,909 raw records to 392,692 valid sales items generating £8.88M revenue.
  - Classified 4,338 customers into 4 RFM KMeans segments.
  - Mined 1,030 high-lift association rules.
  - Trained Random Forest Sales Forecaster (R²: 0.3280, MAE: £11,779).
  - Built FAISS RAG Assistant with `all-MiniLM-L6-v2` embeddings.

---

### 🟢 SLIDE 3: Problem Statement
- **Retail Challenges:**
  - Raw transaction data lacks actionable segmentation.
  - High customer acquisition costs require targeted retention of VIP vs. At Risk customers.
  - Inefficient cross-selling limits Average Basket Value (ABV).
  - Inaccurate sales forecasts cause inventory overstocking or stockouts.
  - Business stakeholders lack plain natural language interfaces to query data.

---

### 🟢 SLIDE 4: Technology Stack & Modular Architecture
- **Programming & Libraries:** Python 3.14, Pandas, NumPy, Scikit-Learn, FP-Growth (`mlxtend`), Plotly, Joblib.
- **AI & RAG:** Sentence Transformers (`all-MiniLM-L6-v2`), FAISS Vector Database, HuggingFace Transformers (`flan-t5-small`).
- **Web Dashboard:** Streamlit (Multi-page, Responsive Glassmorphic Dark Theme CSS).
- **Architecture:** Modular Python backend (`utils/`), Cached Models (`models/`), Processed Data (`data/processed/`), Vector Database (`vector_db/`).

---

### 🟢 SLIDE 5: Module 1 & 2 - Data Understanding & Cleaning
- **Raw Log Shape:** 541,909 rows × 8 columns.
- **Data Cleaning Steps:**
  - Removed duplicate rows (5,268 rows).
  - Removed missing CustomerIDs (135,080 rows).
  - Removed cancelled invoices starting with 'C'.
  - Filtered out non-positive quantities and prices.
- **Engineered Features:** `TotalPrice = Quantity × UnitPrice`, `Year`, `Month`, `Day`, `Weekday`, `Hour`.
- **Cleaned Dataset:** 392,692 rows, £8,887,208.89 revenue, 4,338 unique customers.

---

### 🟢 SLIDE 6: Module 3 - Exploratory Data Analysis (EDA)
- **Top Product:** `PAPER CRAFT , LITTLE BIRDIE` (£168,469.60).
- **Top Customer:** Customer ID `18102` (£259,657.30).
- **Geographic Dominance:** United Kingdom accounts for >84% of revenue.
- **Peak Sales Times:** Thursdays generate highest revenue; peak purchasing hours occur between 11:00 AM – 1:00 PM.

---

### 🟢 SLIDE 7: Module 4 - Customer Segmentation (RFM + KMeans)
- **RFM Methodology:**
  - **Recency ($R$):** Days since last order.
  - **Frequency ($F$):** Total orders placed.
  - **Monetary ($M$):** Total spending (£).
- **KMeans Clustering ($k=4$):** Standardized & log-transformed feature space.
- **Segments:**
  - 👑 **VIP Customers (713):** High frequency, massive spend.
  - 💎 **Loyal Customers (837):** Regular repeat purchasers.
  - 🎯 **Regular Customers (1,166):** Moderate activity.
  - ⚠️ **At Risk Customers (1,622):** Inactive long window (Win-back target).

---

### 🟢 SLIDE 8: Module 5 & 6 - Market Basket Analysis & Recommendations
- **Algorithm:** FP-Growth on binary transaction matrix.
- **Key Metrics:** Support, Confidence, Lift.
- **Rules Mined:** 1,030 association rules with Lift up to 8.5+.
- **Recommender Engine:** Input product name $\rightarrow$ Top 5 cross-selling co-purchased items (with bestseller fallback).
- **Example:** Searching `WHITE HANGING HEART T-LIGHT HOLDER` recommends `RED HANGING HEART T-LIGHT HOLDER`.

---

### 🟢 SLIDE 9: Module 7 - Sales Prediction (Random Forest)
- **Daily Sales Aggregation:** Total daily revenue over 305 operational days.
- **Features:** Calendar variables (`DayOfWeek`, `Month`, `Day`, `Is_Weekend`), Lag features (`lag_1`, `lag_7`, `lag_14`, `lag_30`), Rolling averages (`rolling_7`, `rolling_14`).
- **Evaluation:**
  - **MAE:** £11,779.68
  - **RMSE:** £21,785.21
  - **R² Score:** 0.3280
- **Horizon Slider:** Interactive 1 to 30 day future daily revenue projection.

---

### 🟢 SLIDE 10: Module 8 - AI Assistant (RAG Vector DB)
- **Vector Embeddings:** 384-dimensional embeddings using `SentenceTransformer('all-MiniLM-L6-v2')`.
- **Vector Database:** FAISS Index (`vector_db/faiss_index.bin`).
- **Query Pipeline:** Semantic vector search over retail knowledge base + natural language answer generation.
- **Sample Query:** *"Which products generated highest revenue?"* $\rightarrow$ Accurately returns top revenue items & revenue totals.

---

### 🟢 SLIDE 11: Module 9 - Streamlit Dashboard UI Demo
- **Theme:** Glassmorphism obsidian theme with glowing borders and custom Plus Jakarta Sans font.
- **Features:**
  - 8 Sidebar Navigation Tabs (`Executive Overview`, `Sales Analytics`, `Customer Segmentation`, `Market Basket`, `Recommender`, `Sales Prediction`, `AI Assistant`, `Reports`).
  - Dynamic Date Range & Country Multi-Select filters.
  - Instant CSV downloads for datasets, segments, rules, and forecasts.

---

### 🟢 SLIDE 12: Live Demo Walkthrough
- *Demonstration of live Streamlit dashboard running on `http://localhost:8501`.*
- **Step 1:** Executive Overview KPI cards & Plotly trends.
- **Step 2:** Interactive 3D RFM scatter plot & segment lookup.
- **Step 3:** Product recommender input search.
- **Step 4:** Daily sales forecast horizon adjustment.
- **Step 5:** Asking business questions to RAG AI Assistant.

---

### 🟢 SLIDE 13: Conclusion & Key Takeaways
- Successfully delivered a full-stack, AI-driven retail intelligence platform.
- Combines classical ML (KMeans, FP-Growth, Random Forest) with modern Generative AI / RAG (FAISS, Sentence Transformers).
- Scalable, modular code structure ready for enterprise deployment.

---

### 🟢 SLIDE 14: Questions & Answers (Defense Viva)
- Thank You!
- Open for Questions & Evaluation.
