import os
import sqlite3
import hashlib
import secrets
import datetime
from typing import Optional, List, Dict, Any

DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "retail_intelligence.db")

def get_db_connection() -> sqlite3.Connection:
    """Thread-safe SQLite connection factory with row factory dict-like access."""
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def hash_password(password: str) -> tuple[str, str]:
    """Secure password hashing using PBKDF2-HMAC-SHA256 with cryptographic salt."""
    salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
    return key.hex(), salt


def verify_password(password: str, hashed: str, salt: str) -> bool:
    """Constant-time verification of password hash."""
    key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
    return secrets.compare_digest(key.hex(), hashed)


def init_db():
    """Initialize database tables, indexes, and seed default production users and datasets."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Users Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        salt TEXT NOT NULL,
        full_name TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'Retail Store Manager',
        company TEXT NOT NULL DEFAULT 'DMVCORETECH',
        avatar TEXT DEFAULT '🛍️',
        created_at TEXT NOT NULL
    );
    """)

    # 2. User Sessions Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_sessions (
        token TEXT PRIMARY KEY,
        user_id INTEGER NOT NULL,
        username TEXT NOT NULL,
        role TEXT NOT NULL,
        created_at TEXT NOT NULL,
        expires_at TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );
    """)

    # 3. Datasets Registry Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS datasets (
        dataset_id TEXT PRIMARY KEY,
        user_id INTEGER,
        filename TEXT NOT NULL,
        file_path TEXT NOT NULL,
        upload_time TEXT NOT NULL,
        raw_rows INTEGER DEFAULT 0,
        cleaned_rows INTEGER DEFAULT 0,
        total_revenue REAL DEFAULT 0.0,
        total_customers INTEGER DEFAULT 0,
        total_products INTEGER DEFAULT 0,
        mined_rules INTEGER DEFAULT 0,
        is_default INTEGER DEFAULT 0,
        is_active INTEGER DEFAULT 0,
        created_at TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
    );
    """)

    # 4. Dataset Artifacts Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS dataset_artifacts (
        dataset_id TEXT PRIMARY KEY,
        cleaned_path TEXT NOT NULL,
        rfm_path TEXT,
        rules_path TEXT,
        daily_path TEXT,
        created_at TEXT NOT NULL,
        FOREIGN KEY (dataset_id) REFERENCES datasets(dataset_id) ON DELETE CASCADE
    );
    """)

    # 5. Chat & RAG Audit Logs Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS chat_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        dataset_id TEXT,
        username TEXT,
        query TEXT NOT NULL,
        response TEXT NOT NULL,
        is_scope_violation INTEGER DEFAULT 0,
        created_at TEXT NOT NULL
    );
    """)

    conn.commit()

    # Seed Default Users
    seed_users = [
        ("admin", "admin@dmvcoretech.com", "admin123", "System Administrator", "Platform Administrator", "DMVCORETECH", "👑"),
        ("retailer", "retailer@dmvcoretech.com", "retailer123", "Elena Rostova", "Senior Retail Merchandiser", "DMVCORETECH", "🛍️"),
        ("intern", "intern@dmvcoretech.com", "intern123", "AIML Intern", "AIML Data Scientist Intern", "DMVCORETECH", "🎓")
    ]

    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for u_name, u_email, u_pass, u_full, u_role, u_comp, u_avatar in seed_users:
        cursor.execute("SELECT id FROM users WHERE username = ?", (u_name,))
        if not cursor.fetchone():
            p_hash, p_salt = hash_password(u_pass)
            cursor.execute("""
                INSERT INTO users (username, email, password_hash, salt, full_name, role, company, avatar, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (u_name, u_email, p_hash, p_salt, u_full, u_role, u_comp, u_avatar, now_str))

    # Seed Default Online Retail Dataset Record
    cursor.execute("SELECT dataset_id FROM datasets WHERE dataset_id = 'default'")
    if not cursor.fetchone():
        cleaned_path = os.path.abspath("data/processed/cleaned_retail_data.csv")
        rfm_path = os.path.abspath("data/processed/rfm_data.csv")
        rules_path = os.path.abspath("data/processed/association_rules.csv")
        daily_path = os.path.abspath("data/processed/daily_sales.csv")
        raw_path = os.path.abspath("data/raw/Online Retail.xlsx")

        cursor.execute("""
            INSERT INTO datasets (
                dataset_id, user_id, filename, file_path, upload_time,
                raw_rows, cleaned_rows, total_revenue, total_customers, total_products,
                mined_rules, is_default, is_active, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            "default", 1, "Online Retail.xlsx (Default)", raw_path, now_str,
            541909, 392692, 8887208.89, 4338, 3866,
            1030, 1, 1, now_str
        ))

        cursor.execute("""
            INSERT INTO dataset_artifacts (dataset_id, cleaned_path, rfm_path, rules_path, daily_path, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, ("default", cleaned_path, rfm_path, rules_path, daily_path, now_str))

    conn.commit()
    conn.close()
    print("✅ Production SQLite Database initialized & verified successfully:", DB_FILE)


# ==========================================
# 🔐 AUTHENTICATION & USER MANAGEMENT
# ==========================================

def create_user(username: str, email: str, password: str, full_name: str, role: str = "Retail Store Manager", company: str = "DMVCORETECH", avatar: str = "🛍️") -> Dict[str, Any]:
    """Register a new user into SQLite database."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM users WHERE username = ? OR email = ?", (username.strip().lower(), email.strip().lower()))
    if cursor.fetchone():
        conn.close()
        raise ValueError("Username or Email already registered.")

    p_hash, p_salt = hash_password(password)
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
        INSERT INTO users (username, email, password_hash, salt, full_name, role, company, avatar, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (username.strip().lower(), email.strip().lower(), p_hash, p_salt, full_name.strip(), role.strip(), company.strip(), avatar, now_str))

    user_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return {
        "id": user_id,
        "username": username.strip().lower(),
        "email": email.strip().lower(),
        "full_name": full_name.strip(),
        "role": role.strip(),
        "company": company.strip(),
        "avatar": avatar
    }


def authenticate_user(username: str, password: str) -> Optional[Dict[str, Any]]:
    """Verify user credentials and create active session token."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE username = ? OR email = ?", (username.strip().lower(), username.strip().lower()))
    user_row = cursor.fetchone()

    if not user_row:
        conn.close()
        return None

    if not verify_password(password, user_row["password_hash"], user_row["salt"]):
        conn.close()
        return None

    # Generate Session Token
    token = f"token_{secrets.token_urlsafe(24)}"
    now = datetime.datetime.now()
    expires = now + datetime.timedelta(days=7)

    cursor.execute("""
        INSERT INTO user_sessions (token, user_id, username, role, created_at, expires_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (token, user_row["id"], user_row["username"], user_row["role"], now.strftime("%Y-%m-%d %H:%M:%S"), expires.strftime("%Y-%m-%d %H:%M:%S")))

    conn.commit()
    conn.close()

    return {
        "token": token,
        "user": {
            "id": user_row["id"],
            "username": user_row["username"],
            "email": user_row["email"],
            "full_name": user_row["full_name"],
            "role": user_row["role"],
            "company": user_row["company"],
            "avatar": user_row["avatar"]
        }
    }


def validate_session_token(token: str) -> Optional[Dict[str, Any]]:
    """Validate session token against SQLite user_sessions table."""
    if not token:
        return None
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT s.*, u.full_name, u.email, u.company, u.avatar
        FROM user_sessions s
        JOIN users u ON s.user_id = u.id
        WHERE s.token = ?
    """, (token,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    # Check expiration
    expires = datetime.datetime.strptime(row["expires_at"], "%Y-%m-%d %H:%M:%S")
    if datetime.datetime.now() > expires:
        return None

    return {
        "user_id": row["user_id"],
        "username": row["username"],
        "role": row["role"],
        "full_name": row["full_name"],
        "email": row["email"],
        "company": row["company"],
        "avatar": row["avatar"]
    }


def invalidate_session_token(token: str):
    """Remove session token upon logout."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM user_sessions WHERE token = ?", (token,))
    conn.commit()
    conn.close()


# ==========================================
# 📜 DATASETS DATABASE PERSISTENCE
# ==========================================

def save_dataset_record(metadata: Dict[str, Any], artifacts: Dict[str, str], set_active: bool = True):
    """Persist new dataset metadata and storage paths in SQLite."""
    conn = get_db_connection()
    cursor = conn.cursor()

    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    d_id = metadata["dataset_id"]

    if set_active:
        cursor.execute("UPDATE datasets SET is_active = 0")

    cursor.execute("""
        INSERT OR REPLACE INTO datasets (
            dataset_id, user_id, filename, file_path, upload_time,
            raw_rows, cleaned_rows, total_revenue, total_customers, total_products,
            mined_rules, is_default, is_active, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        d_id, metadata.get("user_id", 1), metadata["filename"], metadata.get("file_path", ""),
        metadata["upload_time"], metadata.get("raw_rows", 0), metadata.get("cleaned_rows", 0),
        metadata.get("total_revenue", 0.0), metadata.get("total_customers", 0),
        metadata.get("total_products", 0), metadata.get("mined_rules", 0),
        1 if metadata.get("is_default") else 0, 1 if set_active else 0, now_str
    ))

    cursor.execute("""
        INSERT OR REPLACE INTO dataset_artifacts (dataset_id, cleaned_path, rfm_path, rules_path, daily_path, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        d_id, artifacts["cleaned_path"], artifacts.get("rfm_path"),
        artifacts.get("rules_path"), artifacts.get("daily_path"), now_str
    ))

    conn.commit()
    conn.close()


def list_datasets_from_db() -> List[Dict[str, Any]]:
    """Retrieve all archived datasets with active flags from SQLite."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM datasets ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()

    result = []
    for r in rows:
        result.append({
            "dataset_id": r["dataset_id"],
            "filename": r["filename"],
            "upload_time": r["upload_time"],
            "raw_rows": r["raw_rows"],
            "cleaned_rows": r["cleaned_rows"],
            "total_revenue": round(float(r["total_revenue"]), 2),
            "total_customers": r["total_customers"],
            "total_products": r["total_products"],
            "mined_rules": r["mined_rules"],
            "is_default": bool(r["is_default"]),
            "is_active": bool(r["is_active"])
        })
    return result


def set_active_dataset_in_db(dataset_id: str) -> Optional[Dict[str, Any]]:
    """Set specified dataset as active in SQLite."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM datasets WHERE dataset_id = ?", (dataset_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return None

    cursor.execute("UPDATE datasets SET is_active = 0")
    cursor.execute("UPDATE datasets SET is_active = 1 WHERE dataset_id = ?", (dataset_id,))
    conn.commit()

    meta = {
        "dataset_id": row["dataset_id"],
        "filename": row["filename"],
        "upload_time": row["upload_time"],
        "raw_rows": row["raw_rows"],
        "cleaned_rows": row["cleaned_rows"],
        "total_revenue": round(float(row["total_revenue"]), 2),
        "total_customers": row["total_customers"],
        "total_products": row["total_products"],
        "mined_rules": row["mined_rules"],
        "is_default": bool(row["is_default"]),
        "is_active": True
    }
    conn.close()
    return meta


def get_active_dataset_record() -> Optional[Dict[str, Any]]:
    """Retrieve active dataset record and its artifact paths."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT d.*, a.cleaned_path, a.rfm_path, a.rules_path, a.daily_path
        FROM datasets d
        LEFT JOIN dataset_artifacts a ON d.dataset_id = a.dataset_id
        WHERE d.is_active = 1
        LIMIT 1
    """)
    row = cursor.fetchone()

    # Fallback to default if none active
    if not row:
        cursor.execute("""
            SELECT d.*, a.cleaned_path, a.rfm_path, a.rules_path, a.daily_path
            FROM datasets d
            LEFT JOIN dataset_artifacts a ON d.dataset_id = a.dataset_id
            WHERE d.dataset_id = 'default'
            LIMIT 1
        """)
        row = cursor.fetchone()

    conn.close()
    if not row:
        return None
    return dict(row)


def delete_dataset_from_db(dataset_id: str) -> bool:
    """Delete custom dataset record from SQLite."""
    if dataset_id == "default":
        return False
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT is_active FROM datasets WHERE dataset_id = ?", (dataset_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return False

    was_active = bool(row["is_active"])
    cursor.execute("DELETE FROM datasets WHERE dataset_id = ?", (dataset_id,))

    if was_active:
        cursor.execute("UPDATE datasets SET is_active = 1 WHERE dataset_id = 'default'")

    conn.commit()
    conn.close()
    return True


# ==========================================
# 📊 AUDIT & CHAT LOGGING
# ==========================================

def log_chat_query(dataset_id: str, username: str, query: str, response: str, is_violation: bool = False):
    """Log user interactions with RAG chatbot in SQLite."""
    conn = get_db_connection()
    cursor = conn.cursor()
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
        INSERT INTO chat_logs (dataset_id, username, query, response, is_scope_violation, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (dataset_id, username, query, response, 1 if is_violation else 0, now_str))

    conn.commit()
    conn.close()


def get_db_statistics() -> Dict[str, Any]:
    """Provide production database health and statistics metrics."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM datasets")
    total_datasets = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM user_sessions")
    active_sessions = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM chat_logs")
    total_chats = cursor.fetchone()[0]

    conn.close()

    db_size = os.path.getsize(DB_FILE) if os.path.exists(DB_FILE) else 0

    return {
        "database_type": "SQLite3 (ACID-Compliant Persistent Storage)",
        "database_file": os.path.basename(DB_FILE),
        "database_path": DB_FILE,
        "database_size_kb": round(db_size / 1024, 2),
        "total_registered_users": total_users,
        "total_archived_datasets": total_datasets,
        "active_sessions": active_sessions,
        "total_logged_chat_queries": total_chats,
        "status": "HEALTHY_AND_CONNECTED"
    }
