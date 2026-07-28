import os
import sys
import pandas as pd

from utils.data_loader import clean_data, get_dataset_summary
from utils.segmentation import train_customer_segmentation
from utils.market_basket import generate_market_basket_rules
from utils.sales_prediction import train_sales_forecaster
from utils.rag_assistant import get_rag_assistant


def main():
    print("=" * 70)
    print("🚀 AI RETAIL INTELLIGENCE PLATFORM - DATA & MODEL PIPELINE")
    print("=" * 70)
    
    # 1. Clean Data
    print("\n[MODULE 1 & 2] Cleaning Raw Dataset...")
    cleaned_df = clean_data(save_processed=True)
    summary = get_dataset_summary(cleaned_df)
    print(f"✅ Cleaned Dataset Shape: {summary['shape']}")
    print(f"✅ Total Revenue: £{cleaned_df['TotalPrice'].sum():,.2f}")
    print(f"✅ Unique Customers: {summary['unique_customers']}")
    print(f"✅ Unique Products: {summary['unique_products']}")
    
    # 2. Customer Segmentation
    print("\n[MODULE 4] Training Customer Segmentation (RFM + KMeans)...")
    rfm_df = train_customer_segmentation(cleaned_df, n_clusters=4)
    print(f"✅ Customer Segmentation complete. Segments distribution:")
    print(rfm_df['Segment'].value_counts())
    
    # 3. Market Basket Analysis
    print("\n[MODULE 5 & 6] Mining Association Rules (Apriori/FP-Growth)...")
    rules_df = generate_market_basket_rules(cleaned_df, min_support=0.01, min_threshold=0.2)
    print(f"✅ Association Rules Mined: {len(rules_df)} rules generated.")
    
    # 4. Sales Prediction
    print("\n[MODULE 7] Training Sales Forecasting Model (Random Forest)...")
    eval_results = train_sales_forecaster(cleaned_df)
    print(f"✅ Sales Forecast Evaluation -> MAE: £{eval_results['mae']:,.2f} | RMSE: £{eval_results['rmse']:,.2f} | R²: {eval_results['r2']:.4f}")
    
    # 5. RAG AI Assistant Vector Store
    print("\n[MODULE 8] Building RAG Knowledge Base & FAISS Vector Store...")
    assistant = get_rag_assistant()
    assistant.build_knowledge_base(cleaned_df, rules_df, rfm_df)
    print("✅ FAISS Vector Database initialized successfully.")
    
    # 6. Export Reports
    print("\n[REPORTS] Exporting Analytics & Forecast Reports...")
    reports_dir = "reports"
    os.makedirs(reports_dir, exist_ok=True)
    
    # Summary CSV
    summary_df = pd.DataFrame([{
        "Total_Revenue_GBP": cleaned_df['TotalPrice'].sum(),
        "Total_Orders": cleaned_df['InvoiceNo'].nunique(),
        "Total_Customers": cleaned_df['CustomerID'].nunique(),
        "Total_Products": cleaned_df['StockCode'].nunique(),
        "Average_Order_Value": cleaned_df['TotalPrice'].sum() / cleaned_df['InvoiceNo'].nunique(),
        "MAE": eval_results['mae'],
        "RMSE": eval_results['rmse'],
        "R2_Score": eval_results['r2']
    }])
    summary_df.to_csv(os.path.join(reports_dir, "retail_analytics_summary.csv"), index=False)
    
    # Association Rules Top 20 Report
    rules_df.head(20).to_csv(os.path.join(reports_dir, "top_20_association_rules.csv"), index=False)
    
    # Customer Segment Summary Report
    rfm_df.to_csv(os.path.join(reports_dir, "customer_segments_rfm.csv"), index=False)
    
    print("✅ Reports exported to 'reports/' directory.")
    print("=" * 70)
    print("🎉 ALL MODULE PIPELINES EXECUTED SUCCESSFULLY!")
    print("=" * 70)

if __name__ == "__main__":
    main()
