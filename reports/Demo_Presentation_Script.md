# 🎙️ LIVE DEMO PRESENTATION SCRIPT
# AI Retail Intelligence Platform - Major Project Defense

---

## ⏱️ PRESENTATION TIME ALLOCATION (10–12 MINUTES)

| Section | Topic | Allocated Time |
|---|---|---|
| **Part 1** | Introduction & Problem Statement | 1.5 Minutes |
| **Part 2** | System Architecture & Dataset Preprocessing | 2.0 Minutes |
| **Part 3** | Live Dashboard Demo: Executive Overview & EDA | 2.0 Minutes |
| **Part 4** | Live Dashboard Demo: RFM Segmentation & Market Basket Recommender | 2.5 Minutes |
| **Part 5** | Live Dashboard Demo: Random Forest Forecast & RAG AI Assistant | 2.5 Minutes |
| **Part 6** | Conclusion & Q&A | 1.5 Minutes |

---

## 📜 STEP-BY-STEP PRESENTATION SCRIPT

### 🎬 PART 1: INTRODUCTION & OVERVIEW (0:00 - 1:30)
**Presenter Speaking Script:**
> *"Respected Examiners, Faculty Members, and Peers—Good morning/afternoon. Today, I am proud to present my final-year major project: **AI Retail Intelligence Platform: Sales Analytics, Customer Segmentation, Market Basket Analysis, Product Recommendation, Sales Prediction, and AI Assistant**.*
>
> *In today's retail landscape, companies generate millions of raw transaction logs daily. However, without automated intelligent pipelines, key revenue opportunities are lost. Our platform transforms raw transaction logs into real-time business strategy by combining Unsupervised Machine Learning, Association Rule Mining, Supervised Sales Forecasting, and Retrieval-Augmented Generation (RAG) AI Assistants."*

---

### ⚙️ PART 2: ARCHITECTURE & PREPROCESSING (1:30 - 3:30)
**Presenter Speaking Script:**
> *"Let us briefly look at the underlying data pipeline. We utilized the UCI Online Retail Dataset, comprising 541,909 raw records. Through our automated data loader and cleaning module (`utils/data_loader.py`), we filtered out cancelled orders, missing CustomerIDs, and invalid quantities, yielding 392,692 cleaned transaction line items generating over £8.88 Million in total gross revenue across 4,338 customers and 3,665 unique SKUs.
>
> The codebase is modularly structured into separate utility packages, cached machine learning models in `models/`, an indexed vector database in `vector_db/`, and a responsive multi-page Streamlit web dashboard."*

---

### 🖥️ PART 3: LIVE DEMO - OVERVIEW & EDA (3:30 - 5:30)
**Action:** Open Browser at `http://localhost:8501`.

**Presenter Speaking Script:**
> *"Now, let us navigate to our live interactive application. Here on the **Executive Overview** screen, you see five primary KPI cards displaying Total Revenue (£8.89M), Total Orders (18.5k), Active Customers (4,338), Catalog SKUs (3,665), and Average Order Value (£479.56).
>
> On the left sidebar, we can dynamically filter the dataset by country or date range. For instance, filtering for the United Kingdom automatically updates every monthly revenue chart, top product bar chart, and customer ranking in real time."*

---

### 👥 PART 4: LIVE DEMO - SEGMENTATION & MARKET BASKET (5:30 - 8:00)
**Action:** Click on `👥 Customer RFM Segmentation` in sidebar.

**Presenter Speaking Script:**
> *"Next, let us explore **Customer Segmentation**. We computed Recency, Frequency, and Monetary (RFM) parameters for every customer, applied log transformations, standardized the feature space, and trained a KMeans clustering algorithm with $k=4$.
>
> The model automatically classified customers into four action-oriented segments:
> - **VIP Customers (713):** High-frequency, top revenue drivers.
> - **Loyal Customers (837):** Steady repeat buyers.
> - **Regular Customers (1,166):** Moderate shoppers.
> - **At Risk Customers (1,622):** Customers with high recency who haven't purchased recently, allowing marketing teams to launch targeted win-back campaigns.
>
> Now moving to **Market Basket Analysis & Product Recommendations**—using the FP-Growth algorithm, we mined 1,030 association rules. In the Recommendation engine, if we select a product like `'WHITE HANGING HEART T-LIGHT HOLDER'`, the system instantaneously returns top co-purchased items such as `'RED HANGING HEART T-LIGHT HOLDER'` with high lift metrics."*

---

### 🤖 PART 5: LIVE DEMO - FORECASTING & RAG ASSISTANT (8:00 - 10:30)
**Action:** Click on `📊 Sales Prediction (RF)` and then `💬 AI Assistant (RAG)`.

**Presenter Speaking Script:**
> *"In the **Sales Prediction** module, we aggregated daily total revenue over 305 operating days and engineered calendar variables, 30-day lag features, and rolling averages. Our Random Forest Regressor achieved a Mean Absolute Error of £11,779 on daily revenue. Using the horizon slider, managers can forecast sales 7, 14, or 30 days into the future for proactive inventory management.
>
> Finally, let us look at our **RAG AI Assistant**. Built using Sentence Transformers (`all-MiniLM-L6-v2`) and indexed in a FAISS vector database, non-technical executives can ask plain natural language questions. For example, typing *'Which products generated highest revenue?'* retrieves relevant vectors and returns exact, structured answers instantly."*

---

### 🎯 PART 6: CONCLUSION & VIVA DEFENSE (10:30 - 12:00)
**Presenter Speaking Script:**
> *"In summary, the AI Retail Intelligence Platform delivers an enterprise-ready, end-to-end data science application suitable for real-world retail operations. All reports can be exported directly via the Reports tab.
>
> Thank you for your time and attention. I am now open to your questions and feedback."*
