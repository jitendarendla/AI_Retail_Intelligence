import os
import pandas as pd
import numpy as np
from mlxtend.frequent_patterns import apriori, fpgrowth, association_rules
import plotly.express as px
import plotly.graph_objects as go

RULES_PATH = os.path.join("data", "processed", "association_rules.csv")


def generate_market_basket_rules(df: pd.DataFrame, min_support: float = 0.01, min_threshold: float = 0.2) -> pd.DataFrame:
    """
    Generate transaction basket matrix, run FP-Growth / Apriori algorithm,
    calculate association rules (Support, Confidence, Lift) and cache rules.
    """
    # Create basket matrix (InvoiceNo vs Description)
    print("Building transaction basket matrix...")
    # Filter top 1000 items to keep computation fast and memory efficient
    top_items = df['Description'].value_counts().head(1200).index
    df_filtered = df[df['Description'].isin(top_items)]
    
    basket = (df_filtered.groupby(['InvoiceNo', 'Description'])['Quantity']
              .sum().unstack().reset_index().fillna(0)
              .set_index('InvoiceNo'))
    
    # One-hot encode for mlxtend (True/False or 1/0)
    basket_sets = (basket > 0)
    
    print(f"Running FP-Growth with min_support={min_support}...")
    try:
        frequent_itemsets = fpgrowth(basket_sets, min_support=min_support, use_colnames=True)
    except Exception as e:
        print(f"Fallback to Apriori: {e}")
        frequent_itemsets = apriori(basket_sets, min_support=min_support, use_colnames=True)
        
    if frequent_itemsets.empty:
        print("Warning: No frequent itemsets found with min_support. Lowering threshold...")
        frequent_itemsets = fpgrowth(basket_sets, min_support=0.005, use_colnames=True)
        
    print("Generating Association Rules...")
    rules = association_rules(frequent_itemsets, metric="lift", min_threshold=min_threshold)
    rules = rules.sort_values('lift', ascending=False).reset_index(drop=True)
    
    # Save rules
    os.makedirs(os.path.dirname(RULES_PATH), exist_ok=True)
    
    # Convert frozen sets to strings for storage & display
    rules_to_save = rules.copy()
    rules_to_save['antecedents'] = rules_to_save['antecedents'].apply(lambda x: ', '.join(list(x)))
    rules_to_save['consequents'] = rules_to_save['consequents'].apply(lambda x: ', '.join(list(x)))
    rules_to_save.to_csv(RULES_PATH, index=False)
    
    print(f"Generated {len(rules)} association rules.")
    return rules_to_save


def load_association_rules(df: pd.DataFrame = None) -> pd.DataFrame:
    """Load cached association rules or generate if missing."""
    if os.path.exists(RULES_PATH):
        return pd.read_csv(RULES_PATH)
    elif df is not None:
        return generate_market_basket_rules(df)
    else:
        raise ValueError("Association rules file missing and no DataFrame supplied.")


def recommend_products(product_name: str, rules_df: pd.DataFrame, top_n: int = 5) -> list:
    """
    Recommend top N products based on association rules for an input product name.
    If no exact rule match is found, fallback to co-occurring or top general products.
    """
    if rules_df.empty or product_name is None or product_name.strip() == "":
        return []
    
    query = product_name.strip().upper()
    
    # Search rules where query is in antecedents
    matches = rules_df[rules_df['antecedents'].str.upper().str.contains(query, regex=False, na=False)]
    
    if not matches.empty:
        matches = matches.sort_values(['lift', 'confidence'], ascending=[False, False])
        recommendations = []
        for consequents in matches['consequents']:
            items = [item.strip() for item in consequents.split(',')]
            for item in items:
                if item.upper() != query and item not in recommendations:
                    recommendations.append(item)
                if len(recommendations) >= top_n:
                    break
            if len(recommendations) >= top_n:
                break
        if recommendations:
            return recommendations[:top_n]
            
    # Partial match fallback
    partial_matches = rules_df[rules_df['antecedents'].str.upper().apply(lambda x: any(w in x for w in query.split()))]
    if not partial_matches.empty:
        partial_matches = partial_matches.sort_values(['lift', 'confidence'], ascending=[False, False])
        recommendations = []
        for consequents in partial_matches['consequents']:
            items = [item.strip() for item in consequents.split(',')]
            for item in items:
                if item.upper() != query and item not in recommendations:
                    recommendations.append(item)
                if len(recommendations) >= top_n:
                    break
            if len(recommendations) >= top_n:
                break
        if recommendations:
            return recommendations[:top_n]
            
    return []


def fig_association_rules_scatter(rules_df: pd.DataFrame, top_n: int = 50):
    """Scatter plot of Support vs Confidence vs Lift."""
    df_top = rules_df.head(top_n).copy()
    
    fig = px.scatter(
        df_top, x='support', y='confidence', size='lift', color='lift',
        hover_data=['antecedents', 'consequents'],
        title=f"🛒 Market Basket Analysis: Top {top_n} Rules (Support vs Confidence vs Lift)",
        labels={'support': 'Support', 'confidence': 'Confidence', 'lift': 'Lift'},
        color_continuous_scale='Viridis'
    )
    fig.update_layout(template="plotly_dark", height=450, margin=dict(l=20, r=20, t=50, b=20))
    return fig


def fig_top_lift_rules_bar(rules_df: pd.DataFrame, top_n: int = 15):
    """Bar chart of Top Association Rules by Lift."""
    df_top = rules_df.head(top_n).copy()
    df_top['Rule'] = df_top['antecedents'] + " ➔ " + df_top['consequents']
    df_top = df_top.sort_values('lift', ascending=True)
    
    fig = px.bar(
        df_top, y='Rule', x='lift', orientation='h',
        title=f"🚀 Top {top_n} Association Rules by Lift Score",
        labels={'lift': 'Lift Score', 'Rule': 'Association Rule (Item A ➔ Item B)'},
        color='lift', color_continuous_scale='Plasma'
    )
    fig.update_layout(template="plotly_dark", height=480, margin=dict(l=20, r=20, t=50, b=20))
    return fig
