import os
import pickle
import pandas as pd
import numpy as np

# Optional imports handled gracefully
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

try:
    from transformers import pipeline
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

VECTOR_DIR = "vector_db"
FAISS_INDEX_PATH = os.path.join(VECTOR_DIR, "faiss_index.bin")
METADATA_PATH = os.path.join(VECTOR_DIR, "product_metadata.pkl")


class RAGAssistant:
    def __init__(self, embedding_model_name: str = "all-MiniLM-L6-v2"):
        self.embedding_model_name = embedding_model_name
        self.st_model = None
        self.flan_t5 = None
        self.index = None
        self.documents = []
        self.initialized = False
        
    def _init_models(self):
        if self.initialized:
            return
            
        print("Initializing SentenceTransformer embedding model...")
        if ST_AVAILABLE:
            try:
                self.st_model = SentenceTransformer(self.embedding_model_name)
            except Exception as e:
                print(f"Error loading SentenceTransformer: {e}")
                self.st_model = None
                
        print("Initializing Flan-T5 text generation pipeline...")
        if TRANSFORMERS_AVAILABLE:
            try:
                self.flan_t5 = pipeline(
                    "text-generation", 
                    model="google/flan-t5-small",
                    max_length=256
                )
            except Exception as e:
                print(f"Flan-T5 pipeline load notice: {e}")
                self.flan_t5 = None
                
        self.initialized = True

    def build_knowledge_base(self, df: pd.DataFrame, rules_df: pd.DataFrame = None, rfm_df: pd.DataFrame = None):
        """Construct knowledge documents from dataset analytics."""
        docs = []
        
        # 1. General Sales Summary
        total_rev = df['TotalPrice'].sum()
        total_orders = df['InvoiceNo'].nunique()
        total_cust = df['CustomerID'].nunique()
        total_prod = df['StockCode'].nunique()
        avg_order = total_rev / total_orders if total_orders > 0 else 0
        
        docs.append({
            "topic": "sales_summary",
            "content": f"The Online Retail Platform achieved a total revenue of £{total_rev:,.2f} across {total_orders:,} unique orders and {total_cust:,} customers. The average order value is £{avg_order:.2f} across {total_prod:,} distinct products."
        })
        
        # 2. Top Revenue Products
        top_prods = df.groupby('Description')['TotalPrice'].sum().sort_values(ascending=False).head(15)
        top_prod_str = ", ".join([f"{p} (£{r:,.2f})" for p, r in top_prods.items()])
        docs.append({
            "topic": "top_products",
            "content": f"The top revenue generating products are: {top_prod_str}. The single highest revenue item is '{top_prods.index[0]}' generating £{top_prods.iloc[0]:,.2f}."
        })
        
        # 3. Top Spending Customers
        top_custs = df.groupby('CustomerID')['TotalPrice'].sum().sort_values(ascending=False).head(10)
        top_cust_str = ", ".join([f"Customer {c} (£{r:,.2f})" for c, r in top_custs.items()])
        docs.append({
            "topic": "top_customers",
            "content": f"The top spending customers are: {top_cust_str}. The top individual customer is ID {top_custs.index[0]} with total spend of £{top_custs.iloc[0]:,.2f}."
        })
        
        # 4. Country Sales Breakdown
        country_sales = df.groupby('Country')['TotalPrice'].sum().sort_values(ascending=False).head(10)
        country_str = ", ".join([f"{c} (£{r:,.2f})" for c, r in country_sales.items()])
        docs.append({
            "topic": "country_sales",
            "content": f"The top sales country is United Kingdom with £{country_sales.get('United Kingdom', 0):,.2f}. Top sales countries overall: {country_str}."
        })
        
        # 5. Market Basket & Frequently Bought Together
        if rules_df is not None and not rules_df.empty:
            top_rules = rules_df.head(10)
            rules_str_list = []
            for _, r in top_rules.iterrows():
                rules_str_list.append(f"'{r['antecedents']}' is frequently bought together with '{r['consequents']}' (Lift: {r['lift']:.2f}, Confidence: {r['confidence']:.2%})")
            docs.append({
                "topic": "bought_together",
                "content": "Frequently purchased product combinations from Market Basket Analysis: " + "; ".join(rules_str_list) + "."
            })
            
        # 6. Customer Segments
        if rfm_df is not None and not rfm_df.empty:
            seg_summary = rfm_df.groupby('Segment')['Monetary'].agg(['count', 'sum']).reset_index()
            seg_str = ", ".join([f"{r['Segment']}: {r['count']} customers (£{r['sum']:,.2f} revenue)" for _, r in seg_summary.iterrows()])
            docs.append({
                "topic": "customer_segments",
                "content": f"Customer segmentation breakdown: {seg_str}."
            })
            
        self.documents = docs
        self._index_documents()

    def _index_documents(self):
        """Index documents into FAISS vector database."""
        self._init_models()
        
        texts = [doc['content'] for doc in self.documents]
        
        if self.st_model and FAISS_AVAILABLE:
            try:
                embeddings = self.st_model.encode(texts, convert_to_numpy=True)
                dim = embeddings.shape[1]
                self.index = faiss.IndexFlatL2(dim)
                self.index.add(embeddings.astype('float32'))
                
                os.makedirs(VECTOR_DIR, exist_ok=True)
                faiss.write_index(self.index, FAISS_INDEX_PATH)
                with open(METADATA_PATH, 'wb') as f:
                    pickle.dump(self.documents, f)
                print("FAISS vector database built and saved successfully.")
                return
            except Exception as e:
                print(f"FAISS indexing note: {e}")
                
        # Fallback local storage
        os.makedirs(VECTOR_DIR, exist_ok=True)
        with open(METADATA_PATH, 'wb') as f:
            pickle.dump(self.documents, f)

    def load_vector_db(self):
        """Load vector database metadata and FAISS index if available."""
        if os.path.exists(METADATA_PATH):
            with open(METADATA_PATH, 'rb') as f:
                self.documents = pickle.load(f)
                
        if FAISS_AVAILABLE and os.path.exists(FAISS_INDEX_PATH):
            try:
                self.index = faiss.read_index(FAISS_INDEX_PATH)
            except Exception as e:
                print(f"Could not load FAISS index: {e}")

    def is_domain_question(self, user_question: str) -> bool:
        """Strict domain guardrail check to ensure assistant only answers dataset-related questions."""
        q_lower = user_question.lower().strip()
        
        # Explicit out-of-domain terms (politics, general trivia, code generation, external knowledge)
        out_of_domain_terms = [
            'prime minister', 'pm of', 'president', 'minister', 'capital of',
            'weather', 'movie', 'actor', 'actress', 'cricket', 'football',
            'who is the', 'who was', 'who is', 'politics', 'election', 'government',
            'recipe', 'code for', 'programming', 'python code', 'how to write code',
            'math problem', 'physics', 'chemistry', 'biology', 'quantum', 'space',
            'who created', 'who invented', 'country capital', 'tell me a joke', 'sing a song',
            'modi', 'biden', 'trump', 'sunak', 'starmer', 'curry', 'movie recommendation'
        ]
        
        for term in out_of_domain_terms:
            if term in q_lower:
                return False
                
        # Greetings & identity questions are allowed
        greetings = ['hi', 'hello', 'hey', 'help', 'what can you do', 'who are you', 'capabilities', 'what are you', 'good morning', 'good evening']
        if any(q_lower == g or q_lower.startswith(g + ' ') for g in greetings):
            return True
            
        # Domain keywords related to retail dataset analytics
        domain_keywords = [
            'sale', 'sales', 'revenue', 'product', 'products', 'customer', 'customers',
            'order', 'orders', 'invoice', 'invoices', 'basket', 'recommend', 'recommendation',
            'rfm', 'segment', 'segments', 'segmentation', 'forecast', 'prediction', 'top',
            'total', 'country', 'uk', 'united kingdom', 'buyer', 'buyers', 'price', 'quantity',
            'date', 'month', 'year', 'day', 'hour', 'stat', 'unit', 'growth', 'trend', 'margin',
            'stock', 'sku', 'dataset', 'analysis', 'data', 'upload', 'history', 'store', 'retail',
            'performance', 'most', 'best', 'worst', 'spending', 'frequency', 'recency', 'monetary',
            'lift', 'confidence', 'support', 'predict', 'future', 'insight', 'item', 'items',
            'bought', 'together', 'co-purchased', 'average', 'spend', 'highest', 'lowest',
            'rules', 'association', 'pattern', 'summary', 'overview'
        ]
        
        for kw in domain_keywords:
            if kw in q_lower:
                return True
                
        return False

    def query(self, user_question: str) -> str:
        """
        RAG Query Pipeline with Domain Scope Guardrail:
        1. Validate query domain scope (Reject out-of-domain / non-dataset questions)
        2. Retrieve relevant context from vector database / documents
        3. Synthesize accurate natural language answer
        """
        q_lower = user_question.lower().strip()

        # 1. Check Greetings
        if any(q_lower == g or q_lower.startswith(g + ' ') for g in ['hi', 'hello', 'hey', 'help', 'who are you', 'what can you do']):
            return ("👋 **Hello! Welcome to the AI Retail Intelligence Assistant.**\n\n"
                    "I am specialized strictly in analyzing your uploaded retail datasets, customer RFM segments, market basket recommendations, and sales forecasts.\n\n"
                    "💡 **Ask me questions like:**\n"
                    "• *What is the total revenue and order count in the uploaded dataset?*\n"
                    "• *Which products generated the highest revenue?*\n"
                    "• *What are the top spending customer accounts?*\n"
                    "• *What items are frequently bought together?*\n"
                    "• *Give customer segmentation breakdown.*")

        # 2. Strict Domain Scope Guardrail Check
        if not self.is_domain_question(user_question):
            return ("⚠️ **Scope Guardrail Activated**\n\n"
                    "I am the **AI Retail Intelligence Assistant**. I am strictly configured to answer questions regarding your **uploaded retail datasets and store analytics**.\n\n"
                    "❌ I cannot answer out-of-domain questions (such as general knowledge, politics, external trivia, or code generation).\n\n"
                    "💡 *Please ask a question related to your active retail dataset (e.g. 'Total revenue', 'Top products', or 'Frequently bought together items').*")

        if not self.documents:
            self.load_vector_db()
            
        if not self.documents:
            return "Knowledge base initializing for current dataset. Please ask again in a moment."
            
        # Semantic search using SentenceTransformers + FAISS if ready
        retrieved_contexts = []
        if self.st_model and self.index and FAISS_AVAILABLE:
            try:
                q_emb = self.st_model.encode([user_question], convert_to_numpy=True)
                distances, indices = self.index.search(q_emb.astype('float32'), k=3)
                for idx in indices[0]:
                    if 0 <= idx < len(self.documents):
                        retrieved_contexts.append(self.documents[idx]['content'])
            except Exception as e:
                print(f"Vector search fallback: {e}")
                
        # Keyword context retrieval fallback
        if not retrieved_contexts:
            for doc in self.documents:
                t = doc['topic']
                c = doc['content'].lower()
                if any(k in q_lower for k in ['revenue', 'highest', 'top selling', 'product', 'item']) and t in ['top_products', 'sales_summary']:
                    retrieved_contexts.append(doc['content'])
                elif any(k in q_lower for k in ['customer', 'spend', 'buyer', 'vip', 'loyal', 'rfm']) and t in ['top_customers', 'customer_segments']:
                    retrieved_contexts.append(doc['content'])
                elif any(k in q_lower for k in ['country', 'uk', 'united kingdom', 'location']) and t == 'country_sales':
                    retrieved_contexts.append(doc['content'])
                elif any(k in q_lower for k in ['together', 'basket', 'recommend', 'pair', 'co-purchased']) and t == 'bought_together':
                    retrieved_contexts.append(doc['content'])
                elif any(k in q_lower for k in ['summary', 'total', 'overview', 'order']) and t == 'sales_summary':
                    retrieved_contexts.append(doc['content'])
                    
        if not retrieved_contexts:
            retrieved_contexts = [doc['content'] for doc in self.documents[:2]]
            
        context_str = "\n• ".join(retrieved_contexts)
        
        # Generation via Flan-T5 if model available
        if self.flan_t5:
            try:
                prompt = f"Answer business question based on context:\nContext: {context_str}\nQuestion: {user_question}\nAnswer:"
                res = self.flan_t5(prompt)
                generated = res[0]['generated_text'].strip()
                if len(generated) > 10:
                    return f"💡 **AI Insights:** {generated}\n\n📌 **Active Dataset Context:**\n• {context_str}"
            except Exception as e:
                print(f"Flan-T5 generation note: {e}")
                
        # High quality domain QA response formatting
        return f"💡 **Active Dataset Business Intelligence Insights:**\n\n• {context_str}"


_assistant_instance = None

def get_rag_assistant() -> RAGAssistant:
    """Singleton getter for RAG Assistant."""
    global _assistant_instance
    if _assistant_instance is None:
        _assistant_instance = RAGAssistant()
    return _assistant_instance

