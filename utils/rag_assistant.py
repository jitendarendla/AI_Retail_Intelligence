import os
import re
import pickle
from typing import Optional, List, Dict, Any
import pandas as pd
import numpy as np

# Optional vector/embedding imports handled gracefully
try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False

try:
    from sentence_transformers import SentenceTransformer
    ST_AVAILABLE = True
except ImportError:
    ST_AVAILABLE = False

VECTOR_DIR = "vector_db"
FAISS_INDEX_PATH = os.path.join(VECTOR_DIR, "faiss_index.bin")
METADATA_PATH = os.path.join(VECTOR_DIR, "product_metadata.pkl")


class RAGAssistant:
    def __init__(self, embedding_model_name: str = "all-MiniLM-L6-v2"):
        self.embedding_model_name = embedding_model_name
        self.st_model = None
        self.index = None
        self.documents: List[Dict[str, str]] = []
        self.initialized = False

        # Live active dataset references for exact analytical queries
        self.df: Optional[pd.DataFrame] = None
        self.rules_df: Optional[pd.DataFrame] = None
        self.rfm_df: Optional[pd.DataFrame] = None
        self.dataset_name: str = "Active Dataset"

    def _init_models(self):
        if self.initialized:
            return

        if ST_AVAILABLE:
            try:
                self.st_model = SentenceTransformer(self.embedding_model_name)
            except Exception as e:
                print(f"Embedding model load notice: {e}")
                self.st_model = None

        self.initialized = True

    def bind_active_data(
        self,
        df: Optional[pd.DataFrame],
        rules_df: Optional[pd.DataFrame] = None,
        rfm_df: Optional[pd.DataFrame] = None,
        dataset_name: str = "Active Dataset",
    ):
        """Attach live DataFrames so queries compute exact answers from active data."""
        self.df = df
        self.rules_df = rules_df
        self.rfm_df = rfm_df
        if dataset_name:
            self.dataset_name = dataset_name

    def build_knowledge_base(
        self,
        df: pd.DataFrame,
        rules_df: pd.DataFrame = None,
        rfm_df: pd.DataFrame = None,
        dataset_name: str = "Active Dataset",
    ):
        """Construct human-readable knowledge documents from dataset analytics and bind live tables."""
        self.bind_active_data(df, rules_df, rfm_df, dataset_name=dataset_name)
        docs = []

        if df is None or df.empty:
            self.documents = docs
            return

        # 1. General Sales Summary
        total_rev = float(df["TotalPrice"].sum())
        total_orders = int(df["InvoiceNo"].nunique())
        total_cust = int(df["CustomerID"].nunique())
        total_prod = int(df["StockCode"].nunique())
        total_units = int(df["Quantity"].sum())
        avg_order = total_rev / total_orders if total_orders > 0 else 0.0

        docs.append({
            "topic": "sales_summary",
            "content": (
                f"The active dataset generated £{total_rev:,.2f} in total revenue across "
                f"{total_orders:,} orders and {total_cust:,} customers, totaling {total_units:,} units "
                f"sold across {total_prod:,} distinct products (average order value: £{avg_order:,.2f})."
            ),
        })

        # 2. Top Revenue Products
        top_prods = df.groupby("Description")["TotalPrice"].sum().sort_values(ascending=False).head(15)
        if not top_prods.empty:
            top_prod_str = ", ".join([f"{p} (£{r:,.2f})" for p, r in top_prods.items()])
            docs.append({
                "topic": "top_products",
                "content": (
                    f"The highest-revenue product is '{top_prods.index[0]}' at £{top_prods.iloc[0]:,.2f}. "
                    f"Other leading products include: {top_prod_str}."
                ),
            })

        # 3. Top Spending Customers
        top_custs = df.groupby("CustomerID")["TotalPrice"].sum().sort_values(ascending=False).head(10)
        if not top_custs.empty:
            top_cust_str = ", ".join([f"Customer {c} (£{r:,.2f})" for c, r in top_custs.items()])
            docs.append({
                "topic": "top_customers",
                "content": (
                    f"Customer {top_custs.index[0]} is the highest spender at £{top_custs.iloc[0]:,.2f}. "
                    f"Top spending customers overall: {top_cust_str}."
                ),
            })

        # 4. Market Basket & Frequently Bought Together
        if rules_df is not None and not rules_df.empty:
            top_rules = rules_df.sort_values(["lift", "confidence"], ascending=[False, False]).head(10)
            rules_str_list = []
            for _, r in top_rules.iterrows():
                rules_str_list.append(
                    f"'{r['antecedents']}' is frequently bought with '{r['consequents']}' "
                    f"(confidence {r['confidence']:.1%}, lift {r['lift']:.2f}x)"
                )
            docs.append({
                "topic": "bought_together",
                "content": "Strongest product pairings: " + "; ".join(rules_str_list) + ".",
            })

        # 5. Customer Segments
        if rfm_df is not None and not rfm_df.empty:
            seg_summary = rfm_df.groupby("Segment")["Monetary"].agg(["count", "sum"]).reset_index()
            seg_str = ", ".join(
                [f"{r['Segment']}: {int(r['count']):,} customers (£{r['sum']:,.2f})" for _, r in seg_summary.iterrows()]
            )
            docs.append({
                "topic": "customer_segments",
                "content": f"Customer segment distribution: {seg_str}.",
            })

        # 6. Time Trends
        try:
            dates = pd.to_datetime(df["InvoiceDate"], errors="coerce").dropna()
            if not dates.empty:
                temp = df.loc[dates.index].copy()
                temp["_dt"] = dates
                monthly = temp.groupby(temp["_dt"].dt.to_period("M"))["TotalPrice"].sum()
                best_m = monthly.idxmax()
                docs.append({
                    "topic": "time_trends",
                    "content": (
                        f"Transactions span from {dates.min().strftime('%b %d, %Y')} to {dates.max().strftime('%b %d, %Y')}. "
                        f"The strongest month was {best_m} with £{monthly.max():,.2f} in revenue."
                    ),
                })
        except Exception:
            pass

        self.documents = docs
        self._index_documents()

    def _index_documents(self):
        """Index documents into FAISS vector database."""
        self._init_models()
        texts = [doc["content"] for doc in self.documents]

        if self.st_model and FAISS_AVAILABLE and texts:
            try:
                embeddings = self.st_model.encode(texts, convert_to_numpy=True)
                dim = embeddings.shape[1]
                self.index = faiss.IndexFlatL2(dim)
                self.index.add(embeddings.astype("float32"))

                os.makedirs(VECTOR_DIR, exist_ok=True)
                faiss.write_index(self.index, FAISS_INDEX_PATH)
                with open(METADATA_PATH, "wb") as f:
                    pickle.dump(self.documents, f)
                return
            except Exception as e:
                print(f"FAISS indexing note: {e}")

        os.makedirs(VECTOR_DIR, exist_ok=True)
        with open(METADATA_PATH, "wb") as f:
            pickle.dump(self.documents, f)

    def load_vector_db(self):
        """Load vector database metadata and FAISS index if available."""
        if os.path.exists(METADATA_PATH):
            with open(METADATA_PATH, "rb") as f:
                self.documents = pickle.load(f)

        if FAISS_AVAILABLE and os.path.exists(FAISS_INDEX_PATH):
            try:
                self.index = faiss.read_index(FAISS_INDEX_PATH)
            except Exception as e:
                print(f"Could not load FAISS index: {e}")

    def _find_matching_products(self, query_text: str, limit: int = 5) -> List[str]:
        """Match product names or SKUs from the user's question against active catalog."""
        if self.df is None or self.df.empty:
            return []

        q_lower = query_text.lower().strip()
        prods = [str(p) for p in self.df["Description"].dropna().unique()]

        # 1. Direct full product name containment
        direct = [p for p in prods if len(p) > 3 and p.lower() in q_lower]
        if direct:
            direct.sort(key=len, reverse=True)
            return direct[:limit]

        # 2. Extract meaningful product keywords by stripping conversational filler
        stop_words = {
            "what", "which", "who", "when", "where", "how", "why", "is", "are", "was", "were",
            "the", "a", "an", "for", "of", "in", "on", "to", "with", "and", "or", "by", "from",
            "recommend", "recommendations", "recommended", "suggest", "suggestion", "cross-sell",
            "bought", "together", "with", "pairs", "pair", "buy", "customers", "people", "also",
            "price", "unit", "units", "sold", "revenue", "sales", "total", "average", "avg",
            "tell", "me", "about", "show", "give", "find", "check", "item", "items", "product",
            "products", "many", "much", "did", "do", "does", "often", "frequently", "usually"
        }
        tokens = [t for t in re.findall(r"[a-z0-9\-]+", q_lower) if len(t) >= 3 and t not in stop_words]
        if not tokens:
            return []

        # Score each catalog product by token overlap
        scored = []
        for p in prods:
            p_low = p.lower()
            hits = sum(1 for tok in tokens if tok in p_low)
            if hits > 0:
                # Prefer matches covering a higher fraction of query tokens
                scored.append((hits, -len(p), p))

        if not scored:
            return []

        scored.sort(reverse=True)
        best_hits = scored[0][0]
        # Require at least 2 matching tokens if user provided >= 2 tokens, or 1 if single token
        min_req = 2 if len(tokens) >= 2 else 1
        if best_hits < min_req:
            return []

        return [item[2] for item in scored if item[0] == best_hits][:limit]

    def is_domain_question(self, user_question: str) -> bool:
        """Strict domain guardrail: allow only dataset-related retail analytics & greetings."""
        q_lower = user_question.lower().strip()

        out_of_domain_terms = [
            "prime minister", "pm of", "president", "minister", "capital of",
            "weather", "movie", "actor", "actress", "cricket", "football",
            "who is the", "who was", "politics", "election", "government",
            "recipe", "python code", "how to write code", "javascript code",
            "math problem", "physics", "chemistry", "biology", "quantum",
            "who created", "who invented", "tell me a joke", "sing a song",
            "modi", "biden", "trump", "sunak", "starmer", "movie recommendation",
            "cricket score", "stock market", "bitcoin", "crypto", "sports"
        ]
        for term in out_of_domain_terms:
            if term in q_lower:
                return False

        greetings = [
            "hi", "hello", "hey", "help", "what can you do", "who are you",
            "capabilities", "what are you", "good morning", "good evening", "good afternoon"
        ]
        if any(q_lower == g or q_lower.startswith(g + " ") for g in greetings):
            return True

        domain_keywords = [
            "sale", "sales", "revenue", "product", "products", "customer", "customers",
            "order", "orders", "invoice", "invoices", "basket", "recommend", "recommendation",
            "recommendations", "rfm", "segment", "segments", "segmentation", "forecast",
            "prediction", "predict", "top", "bottom", "lowest", "worst", "best", "total",
            "buyer", "buyers", "price", "quantity", "date", "month", "year", "day", "week",
            "weekday", "weekend", "hour", "hours", "peak", "busiest", "stat", "stats",
            "unit", "units", "growth", "trend", "trends", "margin", "stock", "sku", "skus",
            "dataset", "analysis", "data", "upload", "history", "store", "retail",
            "performance", "most", "spending", "spend", "spent", "frequency", "recency",
            "monetary", "lift", "confidence", "support", "future", "insight", "insights",
            "item", "items", "bought", "together", "co-purchased", "average", "avg", "mean",
            "highest", "rules", "rule", "association", "pattern", "summary", "overview",
            "rows", "records", "transactions", "vip", "loyal", "regular", "at risk", "at-risk",
            "churn", "count", "how many", "how much"
        ]
        if any(kw in q_lower for kw in domain_keywords):
            return True

        # Also allow if the user directly asks about a product in the active catalog
        if self._find_matching_products(user_question, limit=1):
            return True

        return False

    def _extract_top_n(self, q_lower: str, default: int = 5, max_n: int = 15) -> int:
        match = re.search(
            r"\b(?:top|best|worst|lowest|highest|first|which)\s+(\d+)\b|\b(\d+)\s+(?:top|best|highest|lowest|worst|products|items|customers|buyers|sellers)\b",
            q_lower,
        )
        if match:
            val = int(match.group(1) or match.group(2))
            return max(1, min(val, max_n))
        return default

    def _answer_greetings(self) -> str:
        ds_info = ""
        if self.df is not None and not self.df.empty:
            ds_info = f" I am currently connected to **{self.dataset_name}** ({len(self.df):,} cleaned transaction rows)."
        return (
            f"Hello! I am your Retail Analytics Assistant.{ds_info}\n\n"
            "You can ask me questions in plain English about your active dataset, such as:\n"
            "- \"What is our total revenue and average order value?\"\n"
            "- \"Which 5 products earned the most revenue?\"\n"
            "- \"How many VIP and at-risk customers do we have?\"\n"
            "- \"What items are frequently bought together?\"\n"
            "- \"Recommend cross-sell items for WHITE HANGING HEART T-LIGHT HOLDER\"\n"
            "- \"Which month and day of the week perform best?\""
        )

    def _answer_recommendations(self, query_text: str) -> Optional[str]:
        q_lower = query_text.lower()
        is_rec_intent = any(k in q_lower for k in [
            "recommend", "cross-sell", "cross sell", "co-purchased", "bought with",
            "bought together", "pair", "pairs", "alongside", "basket rule", "association"
        ])
        if not is_rec_intent:
            return None

        matched_prods = self._find_matching_products(query_text, limit=3)

        # Case A: Specific product mentioned
        if matched_prods and self.df is not None and not self.df.empty:
            target = matched_prods[0]
            recs_info = []

            if self.rules_df is not None and not self.rules_df.empty:
                m = self.rules_df[
                    self.rules_df["antecedents"].astype(str).str.upper().str.contains(target.upper(), regex=False, na=False)
                ].sort_values(["lift", "confidence"], ascending=[False, False])

                seen = set()
                for _, row in m.iterrows():
                    for item in [x.strip() for x in str(row["consequents"]).split(",")]:
                        if item.upper() != target.upper() and item not in seen:
                            seen.add(item)
                            recs_info.append((item, float(row["confidence"]), float(row["lift"])))
                        if len(recs_info) >= 5:
                            break
                    if len(recs_info) >= 5:
                        break

            if recs_info:
                lines = [
                    f"- **{item}** (confidence: {conf:.1%}, lift: {lift:.2f}x)"
                    for item, conf, lift in recs_info
                ]
                return (
                    f"Based on historical baskets in **{self.dataset_name}**, customers who purchase "
                    f"**{target}** most frequently add these items to the same order:\n\n"
                    + "\n".join(lines)
                )

            # Fallback: compute direct co-occurrence from invoices in df
            target_invoices = self.df[self.df["Description"] == target]["InvoiceNo"].unique()
            if len(target_invoices) > 0:
                co_df = self.df[
                    (self.df["InvoiceNo"].isin(target_invoices)) & (self.df["Description"] != target)
                ]
                co_counts = co_df.groupby("Description")["InvoiceNo"].nunique().sort_values(ascending=False).head(5)
                if not co_counts.empty:
                    lines = [
                        f"- **{item}** (appeared together in {int(cnt):,} orders)"
                        for item, cnt in co_counts.items()
                    ]
                    return (
                        f"In **{self.dataset_name}**, **{target}** appeared in {len(target_invoices):,} orders. "
                        f"The items most commonly bought in the same basket are:\n\n"
                        + "\n".join(lines)
                    )

            return (
                f"I found **{target}** in the catalog, but there are not enough shared multi-item orders "
                f"for it to form strong cross-sell pairings in this dataset."
            )

        # Case B: General market basket / frequently bought together question
        if self.rules_df is not None and not self.rules_df.empty:
            top_rules = self.rules_df.sort_values(["lift", "confidence"], ascending=[False, False]).head(5)
            lines = []
            for _, r in top_rules.iterrows():
                lines.append(
                    f"- **{r['antecedents']}** + **{r['consequents']}** "
                    f"({r['confidence']:.1%} of the time, {r['lift']:.2f}x lift)"
                )
            return (
                f"Across **{len(self.rules_df):,}** mined association rules in **{self.dataset_name}**, "
                f"here are the strongest product pairings frequently bought together:\n\n"
                + "\n".join(lines)
            )

        return "No market basket association rules were found for the active dataset yet."

    def _answer_specific_product(self, query_text: str) -> Optional[str]:
        if self.df is None or self.df.empty:
            return None

        # Avoid hijacking "top products" or "highest revenue product" questions
        q_lower = query_text.lower()
        if any(k in q_lower for k in ["top ", "highest", "best selling", "most popular", "worst", "lowest"]):
            return None

        matched_prods = self._find_matching_products(query_text, limit=3)
        if not matched_prods:
            return None

        target = matched_prods[0]
        sub = self.df[self.df["Description"] == target]
        if sub.empty:
            return None

        rev = float(sub["TotalPrice"].sum())
        units = int(sub["Quantity"].sum())
        orders = int(sub["InvoiceNo"].nunique())
        customers = int(sub["CustomerID"].nunique())
        avg_price = float(sub["UnitPrice"].mean())

        return (
            f"Here are the performance figures for **{target}** in **{self.dataset_name}**:\n\n"
            f"- **Total Revenue:** £{rev:,.2f}\n"
            f"- **Units Sold:** {units:,} units across {orders:,} orders\n"
            f"- **Distinct Buyers:** {customers:,} customers\n"
            f"- **Average Unit Price:** £{avg_price:,.2f}"
        )

    def _answer_top_products(self, q_lower: str) -> Optional[str]:
        if self.df is None or self.df.empty:
            return None

        is_product_q = any(k in q_lower for k in ["product", "products", "item", "items", "sku", "skus", "selling"])
        is_rank_q = any(k in q_lower for k in ["top", "best", "highest", "most", "popular", "worst", "lowest", "least"])
        if not (is_product_q and is_rank_q):
            return None

        n = self._extract_top_n(q_lower, default=5)
        ascending = any(k in q_lower for k in ["worst", "lowest", "least", "bottom"])
        by_units = any(k in q_lower for k in ["quantity", "units", "volume", "most sold", "times sold"])

        metric_col = "Quantity" if by_units else "TotalPrice"
        grouped = (
            self.df.groupby("Description")
            .agg(revenue=("TotalPrice", "sum"), units=("Quantity", "sum"), avg_price=("UnitPrice", "mean"))
            .sort_values("units" if by_units else "revenue", ascending=ascending)
            .head(n)
        )
        if grouped.empty:
            return None

        direction = "lowest" if ascending else "top"
        basis = "units sold" if by_units else "revenue"
        leader = grouped.index[0]
        leader_row = grouped.iloc[0]

        lines = []
        for idx, (name, row) in enumerate(grouped.iterrows(), start=1):
            lines.append(
                f"{idx}. **{name}** — £{row['revenue']:,.2f} revenue ({int(row['units']):,} units, avg £{row['avg_price']:,.2f})"
            )

        return (
            f"Looking at **{self.dataset_name}** by {basis}, **{leader}** leads this list with "
            f"**£{leader_row['revenue']:,.2f}** from **{int(leader_row['units']):,}** units sold.\n\n"
            f"Here are the {direction} {len(grouped)} products by {basis}:\n\n"
            + "\n".join(lines)
        )

    def _answer_segments(self, q_lower: str) -> Optional[str]:
        if not any(k in q_lower for k in ["segment", "rfm", "vip", "loyal", "regular", "at risk", "at-risk", "churn"]):
            return None

        if self.rfm_df is None or self.rfm_df.empty:
            return "Customer segmentation data is not yet available for the active dataset."

        total_cust = len(self.rfm_df)
        total_spend = float(self.rfm_df["Monetary"].sum())

        # Check if user asked about one specific segment
        seg_map = [
            ("vip", "vip", "VIP"),
            ("loyal", "loyal", "Loyal"),
            ("regular", "regular", "Regular"),
            ("at risk", "at risk", "At Risk"),
            ("at-risk", "at risk", "At Risk"),
            ("churn", "at risk", "At Risk"),
        ]
        for q_key, seg_substr, display_label in seg_map:
            if q_key in q_lower and not ("all" in q_lower or "breakdown" in q_lower or "summary" in q_lower):
                sub = self.rfm_df[
                    self.rfm_df["Segment"].astype(str).str.lower().str.replace("-", " ").str.contains(seg_substr, regex=False)
                ]
                if not sub.empty:
                    cnt = len(sub)
                    spend = float(sub["Monetary"].sum())
                    avg_s = float(sub["Monetary"].mean())
                    pct = (cnt / total_cust * 100) if total_cust else 0
                    rev_pct = (spend / total_spend * 100) if total_spend else 0
                    return (
                        f"In **{self.dataset_name}**, there are **{cnt:,} {display_label} customers** "
                        f"({pct:.1f}% of your {total_cust:,} customers).\n\n"
                        f"Together they account for **£{spend:,.2f}** ({rev_pct:.1f}% of total customer spend), "
                        f"with an average lifetime spend of **£{avg_s:,.2f}** per customer."
                    )

        # Full segmentation breakdown
        summary = (
            self.rfm_df.groupby("Segment")["Monetary"]
            .agg(count="count", sum="sum", mean="mean")
            .sort_values("sum", ascending=False)
        )
        lines = []
        for seg, row in summary.iterrows():
            pct = (row["count"] / total_cust * 100) if total_cust else 0
            lines.append(
                f"- **{seg}:** {int(row['count']):,} customers ({pct:.1f}%) — £{row['sum']:,.2f} total spend (avg £{row['mean']:,.2f})"
            )

        return (
            f"Here is the RFM customer segmentation breakdown across all **{total_cust:,}** customers in **{self.dataset_name}**:\n\n"
            + "\n".join(lines)
        )

    def _answer_top_customers(self, q_lower: str) -> Optional[str]:
        if self.df is None or self.df.empty:
            return None

        is_cust_q = any(k in q_lower for k in ["customer", "customers", "buyer", "buyers", "spender", "spenders"])
        is_rank_q = any(k in q_lower for k in ["top", "best", "highest", "most", "biggest"])
        if not (is_cust_q and is_rank_q):
            return None

        n = self._extract_top_n(q_lower, default=5)
        grouped = (
            self.df.groupby("CustomerID")
            .agg(spend=("TotalPrice", "sum"), orders=("InvoiceNo", "nunique"))
            .sort_values("spend", ascending=False)
            .head(n)
        )
        if grouped.empty:
            return None

        lines = []
        for idx, (cid, row) in enumerate(grouped.iterrows(), start=1):
            cid_label = str(int(cid)) if isinstance(cid, (int, float)) and float(cid).is_integer() else str(cid)
            lines.append(
                f"{idx}. **Customer {cid_label}** — £{row['spend']:,.2f} across {int(row['orders']):,} orders"
            )

        top_id = grouped.index[0]
        top_id_lbl = str(int(top_id)) if isinstance(top_id, (int, float)) and float(top_id).is_integer() else str(top_id)
        return (
            f"Your top spending account in **{self.dataset_name}** is **Customer {top_id_lbl}**, "
            f"who spent **£{grouped.iloc[0]['spend']:,.2f}** across {int(grouped.iloc[0]['orders']):,} orders.\n\n"
            f"Top {len(grouped)} customers by total spend:\n\n"
            + "\n".join(lines)
        )

    def _answer_time_trends(self, q_lower: str) -> Optional[str]:
        if self.df is None or self.df.empty:
            return None

        if not any(k in q_lower for k in [
            "month", "monthly", "day", "daily", "week", "weekday", "weekend",
            "hour", "hours", "peak", "busiest", "trend", "trends", "date", "when", "period"
        ]):
            return None

        try:
            dates = pd.to_datetime(self.df["InvoiceDate"], errors="coerce").dropna()
            if dates.empty:
                return "Date timestamps could not be parsed for this dataset."

            temp = self.df.loc[dates.index].copy()
            temp["_dt"] = dates

            monthly = temp.groupby(temp["_dt"].dt.to_period("M"))["TotalPrice"].sum()
            best_month = monthly.idxmax()
            worst_month = monthly.idxmin()

            weekday = temp.groupby(temp["_dt"].dt.day_name())["TotalPrice"].sum()
            best_day = weekday.idxmax()

            hourly = temp.groupby(temp["_dt"].dt.hour)["TotalPrice"].sum()
            best_hour = int(hourly.idxmax())

            return (
                f"Here is what the timeline in **{self.dataset_name}** shows ({dates.min().strftime('%b %d, %Y')} to {dates.max().strftime('%b %d, %Y')}):\n\n"
                f"- **Strongest Month:** {best_month} (£{monthly.max():,.2f} revenue)\n"
                f"- **Quietest Month:** {worst_month} (£{monthly.min():,.2f} revenue)\n"
                f"- **Busiest Day of the Week:** {best_day} (£{weekday.max():,.2f} total sales)\n"
                f"- **Peak Shopping Hour:** {best_hour:02d}:00–{best_hour:02d}:59 (£{hourly.max():,.2f} revenue)"
            )
        except Exception:
            return None

    def _answer_forecast(self, q_lower: str) -> Optional[str]:
        if not any(k in q_lower for k in ["forecast", "predict", "prediction", "future"]):
            return None
        if self.df is None or self.df.empty:
            return "Upload or select a dataset first to inspect its sales forecast."

        try:
            dates = pd.to_datetime(self.df["InvoiceDate"], errors="coerce").dropna()
            temp = self.df.loc[dates.index].copy()
            temp["_date"] = dates.dt.date
            daily = temp.groupby("_date")["TotalPrice"].sum()
            avg_daily = float(daily.mean())
            recent_avg = float(daily.tail(14).mean()) if len(daily) >= 14 else avg_daily
            trend_word = "higher than" if recent_avg >= avg_daily else "lower than"
            return (
                f"Across **{len(daily):,}** active trading days in **{self.dataset_name}**, average daily revenue is "
                f"**£{avg_daily:,.2f}**. Over the most recent 14 days, daily revenue averaged **£{recent_avg:,.2f}** "
                f"({trend_word} the overall historical average).\n\n"
                "You can adjust the interactive 1-to-60 day Random Forest forecast and inspect MAE/RMSE accuracy "
                "metrics in the **Sales Forecast** tab."
            )
        except Exception:
            return "You can view the interactive Random Forest revenue forecast and accuracy metrics in the **Sales Forecast** tab."

    def _answer_summary_or_kpis(self, q_lower: str) -> Optional[str]:
        if self.df is None or self.df.empty:
            return None

        total_rev = float(self.df["TotalPrice"].sum())
        total_orders = int(self.df["InvoiceNo"].nunique())
        total_cust = int(self.df["CustomerID"].nunique())
        total_prod = int(self.df["StockCode"].nunique())
        total_units = int(self.df["Quantity"].sum())
        avg_order = total_rev / total_orders if total_orders > 0 else 0.0
        row_count = len(self.df)

        # Targeted single-metric responses for natural conversation
        if "average order" in q_lower or "aov" in q_lower or "basket size" in q_lower:
            return (
                f"The average order value (AOV) in **{self.dataset_name}** is **£{avg_order:,.2f}**, "
                f"calculated across **{total_orders:,}** orders totaling **£{total_rev:,.2f}**."
            )

        if "how many row" in q_lower or "how many record" in q_lower or "how many transaction" in q_lower:
            return (
                f"**{self.dataset_name}** contains **{row_count:,}** cleaned line-item transactions "
                f"spanning **{total_orders:,}** distinct orders."
            )

        if ("how many customer" in q_lower or "number of customer" in q_lower or "total customer" in q_lower) and "vip" not in q_lower:
            return (
                f"There are **{total_cust:,}** distinct customers recorded in **{self.dataset_name}**, "
                f"who spent an average of **£{(total_rev / total_cust if total_cust else 0):,.2f}** per customer."
            )

        if "how many product" in q_lower or "number of product" in q_lower or "total product" in q_lower or "sku" in q_lower:
            return (
                f"The catalog in **{self.dataset_name}** includes **{total_prod:,}** distinct products (SKUs), "
                f"with **{total_units:,}** total units sold."
            )

        if any(k in q_lower for k in ["revenue", "total sales", "how much did we make", "total order", "summary", "overview", "stat", "insight"]):
            return (
                f"Here is a summary of **{self.dataset_name}**:\n\n"
                f"- **Total Revenue:** £{total_rev:,.2f}\n"
                f"- **Total Orders:** {total_orders:,} (average order value: £{avg_order:,.2f})\n"
                f"- **Active Customers:** {total_cust:,}\n"
                f"- **Catalog Products:** {total_prod:,} distinct items ({total_units:,} units sold)"
            )

        return None

    def query(self, user_question: str) -> str:
        """
        Accurate, human-English Retail Analytics Assistant:
        1. Validates query is within retail dataset scope.
        2. Computes exact answers directly from live dataset DataFrames where applicable.
        3. Falls back cleanly to semantic search over indexed dataset insights.
        """
        q_clean = user_question.strip()
        q_lower = q_clean.lower()

        # 1. Greetings & help
        if any(q_lower == g or q_lower.startswith(g + " ") for g in [
            "hi", "hello", "hey", "help", "who are you", "what can you do", "good morning", "good evening"
        ]):
            return self._answer_greetings()

        # 2. Strict Domain Scope Guardrail
        if not self.is_domain_question(q_clean):
            return (
                "I can only answer questions about your uploaded retail datasets and store analytics "
                "(such as revenue, products, customer segments, market basket pairs, or sales trends). "
                "I am not able to answer general knowledge, political, or unrelated questions."
            )

        # Ensure documents exist if bound data wasn't indexed yet
        if not self.documents and self.df is not None and not self.df.empty:
            self.build_knowledge_base(self.df, self.rules_df, self.rfm_df, dataset_name=self.dataset_name)
        elif not self.documents:
            self.load_vector_db()

        # 3. Run ordered exact analytical handlers
        for handler in (
            lambda: self._answer_recommendations(q_clean),
            lambda: self._answer_top_products(q_lower),
            lambda: self._answer_top_customers(q_lower),
            lambda: self._answer_segments(q_lower),
            lambda: self._answer_specific_product(q_clean),
            lambda: self._answer_time_trends(q_lower),
            lambda: self._answer_forecast(q_lower),
            lambda: self._answer_summary_or_kpis(q_lower),
        ):
            ans = handler()
            if ans:
                return ans

        # 4. Semantic Vector Search Fallback (clean human formatting)
        retrieved_contexts = []
        if self.st_model and self.index and FAISS_AVAILABLE and self.documents:
            try:
                q_emb = self.st_model.encode([q_clean], convert_to_numpy=True)
                distances, indices = self.index.search(q_emb.astype("float32"), k=2)
                for idx in indices[0]:
                    if 0 <= idx < len(self.documents):
                        retrieved_contexts.append(self.documents[idx]["content"])
            except Exception as e:
                print(f"Vector search fallback note: {e}")

        if not retrieved_contexts and self.documents:
            retrieved_contexts = [self.documents[0]["content"]]

        if retrieved_contexts:
            return "Based on the active dataset:\n\n" + "\n\n".join(retrieved_contexts)

        return "The active dataset is still loading. Please try your question again in a moment."


_assistant_instance = None


def get_rag_assistant() -> RAGAssistant:
    """Singleton getter for RAG Assistant."""
    global _assistant_instance
    if _assistant_instance is None:
        _assistant_instance = RAGAssistant()
    return _assistant_instance
