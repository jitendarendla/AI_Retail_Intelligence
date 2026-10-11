import os
import psycopg2
import psycopg2.extras
import hashlib
import secrets
import datetime
from typing import Optional, List, Dict, Any

# PostgreSQL Database Configuration
PG_HOST = os.getenv("PG_HOST", "localhost")
PG_PORT = int(os.getenv("PG_PORT", 5432))
PG_USER = os.getenv("PG_USER", "postgre")
PG_PASSWORD = os.getenv("PG_PASSWORD", "Sonu@801")
PG_DBNAME = os.getenv("PG_DBNAME", "retail_intelligence")

def get_db_connection():
    """Create and return a PostgreSQL connection with DictCursor."""
    try:
        conn = psycopg2.connect(
            host=PG_HOST,
            port=PG_PORT,
            user=PG_USER,
            password=PG_PASSWORD,
            dbname=PG_DBNAME,
            cursor_factory=psycopg2.extras.DictCursor
        )
        return conn
    except Exception as e:
        # Fallback to user 'postgres' if 'postgre' encounters credential issues
        if PG_USER == "postgre":
            try:
                conn = psycopg2.connect(
                    host=PG_HOST,
                    port=PG_PORT,
                    user="postgres",
                    password=PG_PASSWORD,
                    dbname=PG_DBNAME,
                    cursor_factory=psycopg2.extras.DictCursor
                )
                return conn
            except Exception:
                pass
        raise e


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
    """Initialize PostgreSQL database tables, indexes, and seed default production users and datasets."""
    conn = get_db_connection()
    conn.autocommit = True
    cursor = conn.cursor()

    # 1. Users Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        username VARCHAR(100) UNIQUE NOT NULL,
        email VARCHAR(255) UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        salt TEXT NOT NULL,
        full_name VARCHAR(150) NOT NULL,
        role VARCHAR(100) NOT NULL DEFAULT 'Retail Analyst',
        company VARCHAR(100) NOT NULL DEFAULT 'Enterprise Suite',
        avatar TEXT DEFAULT '🛍️',
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 2. User Sessions Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_sessions (
        token VARCHAR(255) PRIMARY KEY,
        user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        username VARCHAR(100) NOT NULL,
        role VARCHAR(100) NOT NULL,
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        expires_at TIMESTAMP NOT NULL
    );
    """)

    # 3. Datasets Registry Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS datasets (
        dataset_id VARCHAR(50) PRIMARY KEY,
        user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
        filename VARCHAR(255) NOT NULL,
        file_path TEXT NOT NULL,
        upload_time VARCHAR(50) NOT NULL,
        raw_rows INTEGER DEFAULT 0,
        cleaned_rows INTEGER DEFAULT 0,
        total_revenue NUMERIC(15, 2) DEFAULT 0.0,
        total_customers INTEGER DEFAULT 0,
        total_products INTEGER DEFAULT 0,
        mined_rules INTEGER DEFAULT 0,
        is_default BOOLEAN DEFAULT FALSE,
        is_active BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 4. Dataset Artifacts Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS dataset_artifacts (
        dataset_id VARCHAR(50) PRIMARY KEY REFERENCES datasets(dataset_id) ON DELETE CASCADE,
        cleaned_path TEXT NOT NULL,
        rfm_path TEXT,
        rules_path TEXT,
        daily_path TEXT,
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 5. Chat & RAG Audit Logs Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS chat_logs (
        id SERIAL PRIMARY KEY,
        dataset_id VARCHAR(50),
        username VARCHAR(100),
        query TEXT NOT NULL,
        response TEXT NOT NULL,
        is_scope_violation BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Seed Default Users in PostgreSQL
    seed_users = [
        ("admin", "admin@retail-ai.com", "admin123", "System Administrator", "Platform Administrator", "Enterprise Suite", "👑"),
        ("retailer", "retailer@retail-ai.com", "retailer123", "Elena Rostova", "Senior Retail Merchandiser", "Enterprise Suite", "🛍️"),
        ("intern", "intern@retail-ai.com", "intern123", "AIML Intern", "AIML Data Scientist Intern", "Enterprise Suite", "🎓")
    ]

    for u_name, u_email, u_pass, u_full, u_role, u_comp, u_avatar in seed_users:
        cursor.execute("SELECT id FROM users WHERE username = %s;", (u_name,))
        if not cursor.fetchone():
            p_hash, p_salt = hash_password(u_pass)
            cursor.execute("""
                INSERT INTO users (username, email, password_hash, salt, full_name, role, company, avatar)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
            """, (u_name, u_email, p_hash, p_salt, u_full, u_role, u_comp, u_avatar))

    # Seed Default Online Retail Dataset Record
    cursor.execute("SELECT dataset_id FROM datasets WHERE dataset_id = 'default';")
    if not cursor.fetchone():
        cleaned_path = os.path.abspath("data/processed/cleaned_retail_data.csv")
        rfm_path = os.path.abspath("data/processed/rfm_data.csv")
        rules_path = os.path.abspath("data/processed/association_rules.csv")
        daily_path = os.path.abspath("data/processed/daily_sales.csv")
        raw_path = os.path.abspath("data/raw/Online Retail.xlsx")
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute("""
            INSERT INTO datasets (
                dataset_id, user_id, filename, file_path, upload_time,
                raw_rows, cleaned_rows, total_revenue, total_customers, total_products,
                mined_rules, is_default, is_active
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
        """, (
            "default", 1, "Online Retail.xlsx (Default)", raw_path, now_str,
            541909, 392692, 8887208.89, 4338, 3866,
            1030, True, True
        ))

        cursor.execute("""
            INSERT INTO dataset_artifacts (dataset_id, cleaned_path, rfm_path, rules_path, daily_path)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (dataset_id) DO UPDATE SET cleaned_path = EXCLUDED.cleaned_path;
        """, ("default", cleaned_path, rfm_path, rules_path, daily_path))

    cursor.close()
    conn.close()
    print("✅ Production PostgreSQL Database connected & initialized successfully on port 5432!")


# ==========================================
# 🔐 AUTHENTICATION & USER MANAGEMENT (PostgreSQL)
# ==========================================

def create_user(username: str, email: str, password: str, full_name: str, role: str = "Retail Analyst", company: str = "Enterprise Suite", avatar: str = "🛍️") -> Dict[str, Any]:
    """Register a new user into PostgreSQL database."""
    conn = get_db_connection()
    conn.autocommit = True
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM users WHERE username = %s OR email = %s;", (username.strip().lower(), email.strip().lower()))
    if cursor.fetchone():
        cursor.close()
        conn.close()
        raise ValueError("Username or Email already registered.")

    p_hash, p_salt = hash_password(password)

    cursor.execute("""
        INSERT INTO users (username, email, password_hash, salt, full_name, role, company, avatar)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id;
    """, (username.strip().lower(), email.strip().lower(), p_hash, p_salt, full_name.strip(), role.strip(), company.strip(), avatar))

    user_id = cursor.fetchone()["id"]
    cursor.close()
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


def get_or_create_google_user(email: str, full_name: str, avatar: Optional[str] = None) -> Dict[str, Any]:
    """Authenticate or register a user through Google OAuth in PostgreSQL."""
    conn = get_db_connection()
    conn.autocommit = True
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE email = %s;", (email.strip().lower(),))
    user_row = cursor.fetchone()

    if user_row:
        user_id = user_row["id"]
        current_avatar = user_row["avatar"]
        if avatar and (not current_avatar or not current_avatar.startswith("http")):
            cursor.execute("UPDATE users SET avatar = %s WHERE id = %s;", (avatar, user_id))
            current_avatar = avatar

        user_dict = {
            "id": user_row["id"],
            "username": user_row["username"],
            "email": user_row["email"],
            "full_name": user_row["full_name"],
            "role": user_row["role"],
            "company": user_row["company"],
            "avatar": current_avatar or "🛍️"
        }
    else:
        # Create unique username from email
        base_username = email.split("@")[0].strip().lower()
        clean_base = "".join(c for c in base_username if c.isalnum() or c in ['_', '.'])
        if not clean_base:
            clean_base = "retail_user"

        candidate = clean_base
        counter = 1
        while True:
            cursor.execute("SELECT id FROM users WHERE username = %s;", (candidate,))
            if not cursor.fetchone():
                break
            candidate = f"{clean_base}_{counter}"
            counter += 1

        username = candidate
        p_hash, p_salt = hash_password(secrets.token_hex(32))
        role = "Retail Analyst"
        company = "Enterprise Suite"
        user_avatar = avatar or "🛍️"

        cursor.execute("""
            INSERT INTO users (username, email, password_hash, salt, full_name, role, company, avatar)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id;
        """, (username, email.strip().lower(), p_hash, p_salt, full_name.strip(), role, company, user_avatar))
        user_id = cursor.fetchone()["id"]

        user_dict = {
            "id": user_id,
            "username": username,
            "email": email.strip().lower(),
            "full_name": full_name.strip(),
            "role": role,
            "company": company,
            "avatar": user_avatar
        }

    # Generate Session Token
    token = f"token_pg_{secrets.token_urlsafe(24)}"
    now = datetime.datetime.now()
    expires = now + datetime.timedelta(days=7)

    cursor.execute("""
        INSERT INTO user_sessions (token, user_id, username, role, created_at, expires_at)
        VALUES (%s, %s, %s, %s, %s, %s);
    """, (token, user_id, user_dict["username"], user_dict["role"], now, expires))

    cursor.close()
    conn.close()

    return {
        "token": token,
        "user": user_dict
    }


def authenticate_user(username: str, password: str) -> Optional[Dict[str, Any]]:
    """Verify user credentials in PostgreSQL and create active session token."""
    conn = get_db_connection()
    conn.autocommit = True
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE username = %s OR email = %s;", (username.strip().lower(), username.strip().lower()))
    user_row = cursor.fetchone()

    if not user_row:
        cursor.close()
        conn.close()
        return None

    if not verify_password(password, user_row["password_hash"], user_row["salt"]):
        cursor.close()
        conn.close()
        return None

    # Generate Session Token
    token = f"token_pg_{secrets.token_urlsafe(24)}"
    now = datetime.datetime.now()
    expires = now + datetime.timedelta(days=7)

    cursor.execute("""
        INSERT INTO user_sessions (token, user_id, username, role, created_at, expires_at)
        VALUES (%s, %s, %s, %s, %s, %s);
    """, (token, user_row["id"], user_row["username"], user_row["role"], now, expires))

    cursor.close()
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
    """Validate session token against PostgreSQL user_sessions table."""
    if not token:
        return None
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT s.*, u.full_name, u.email, u.company, u.avatar
        FROM user_sessions s
        JOIN users u ON s.user_id = u.id
        WHERE s.token = %s;
    """, (token,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()

    if not row:
        return None

    # Check expiration
    if datetime.datetime.now() > row["expires_at"]:
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
    conn.autocommit = True
    cursor = conn.cursor()
    cursor.execute("DELETE FROM user_sessions WHERE token = %s;", (token,))
    cursor.close()
    conn.close()


# ==========================================
# 📜 DATASETS POSTGRESQL PERSISTENCE
# ==========================================

def save_dataset_record(metadata: Dict[str, Any], artifacts: Dict[str, str], set_active: bool = True):
    """Persist new dataset metadata and storage paths in PostgreSQL."""
    conn = get_db_connection()
    conn.autocommit = True
    cursor = conn.cursor()

    d_id = metadata["dataset_id"]

    if set_active:
        cursor.execute("UPDATE datasets SET is_active = FALSE;")

    cursor.execute("""
        INSERT INTO datasets (
            dataset_id, user_id, filename, file_path, upload_time,
            raw_rows, cleaned_rows, total_revenue, total_customers, total_products,
            mined_rules, is_default, is_active
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (dataset_id) DO UPDATE SET
            is_active = EXCLUDED.is_active,
            total_revenue = EXCLUDED.total_revenue,
            cleaned_rows = EXCLUDED.cleaned_rows;
    """, (
        d_id, metadata.get("user_id", 1), metadata["filename"], metadata.get("file_path", ""),
        metadata["upload_time"], metadata.get("raw_rows", 0), metadata.get("cleaned_rows", 0),
        metadata.get("total_revenue", 0.0), metadata.get("total_customers", 0),
        metadata.get("total_products", 0), metadata.get("mined_rules", 0),
        bool(metadata.get("is_default")), set_active
    ))

    cursor.execute("""
        INSERT INTO dataset_artifacts (dataset_id, cleaned_path, rfm_path, rules_path, daily_path)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (dataset_id) DO UPDATE SET
            cleaned_path = EXCLUDED.cleaned_path,
            rfm_path = EXCLUDED.rfm_path,
            rules_path = EXCLUDED.rules_path,
            daily_path = EXCLUDED.daily_path;
    """, (
        d_id, artifacts["cleaned_path"], artifacts.get("rfm_path"),
        artifacts.get("rules_path"), artifacts.get("daily_path")
    ))

    cursor.close()
    conn.close()


def list_datasets_from_db() -> List[Dict[str, Any]]:
    """Retrieve all archived datasets with active flags from PostgreSQL."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM datasets ORDER BY created_at DESC;")
    rows = cursor.fetchall()
    cursor.close()
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
    """Set specified dataset as active in PostgreSQL."""
    conn = get_db_connection()
    conn.autocommit = True
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM datasets WHERE dataset_id = %s;", (dataset_id,))
    row = cursor.fetchone()
    if not row:
        cursor.close()
        conn.close()
        return None

    cursor.execute("UPDATE datasets SET is_active = FALSE;")
    cursor.execute("UPDATE datasets SET is_active = TRUE WHERE dataset_id = %s;", (dataset_id,))

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
    cursor.close()
    conn.close()
    return meta


def get_active_dataset_record() -> Optional[Dict[str, Any]]:
    """Retrieve active dataset record and artifact paths from PostgreSQL."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT d.*, a.cleaned_path, a.rfm_path, a.rules_path, a.daily_path
        FROM datasets d
        LEFT JOIN dataset_artifacts a ON d.dataset_id = a.dataset_id
        WHERE d.is_active = TRUE
        LIMIT 1;
    """)
    row = cursor.fetchone()

    # Fallback to default if none active
    if not row:
        cursor.execute("""
            SELECT d.*, a.cleaned_path, a.rfm_path, a.rules_path, a.daily_path
            FROM datasets d
            LEFT JOIN dataset_artifacts a ON d.dataset_id = a.dataset_id
            WHERE d.dataset_id = 'default'
            LIMIT 1;
        """)
        row = cursor.fetchone()

    cursor.close()
    conn.close()
    if not row:
        return None
    return dict(row)


def delete_dataset_from_db(dataset_id: str) -> bool:
    """Delete custom dataset record from PostgreSQL."""
    if dataset_id == "default":
        return False
    conn = get_db_connection()
    conn.autocommit = True
    cursor = conn.cursor()

    cursor.execute("SELECT is_active FROM datasets WHERE dataset_id = %s;", (dataset_id,))
    row = cursor.fetchone()
    if not row:
        cursor.close()
        conn.close()
        return False

    was_active = bool(row["is_active"])
    cursor.execute("DELETE FROM datasets WHERE dataset_id = %s;", (dataset_id,))

    if was_active:
        cursor.execute("UPDATE datasets SET is_active = TRUE WHERE dataset_id = 'default';")

    cursor.close()
    conn.close()
    return True


# ==========================================
# 📊 AUDIT & CHAT LOGGING (PostgreSQL)
# ==========================================

def log_chat_query(dataset_id: str, username: str, query: str, response: str, is_violation: bool = False):
    """Log user interactions with RAG chatbot into PostgreSQL."""
    try:
        conn = get_db_connection()
        conn.autocommit = True
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO chat_logs (dataset_id, username, query, response, is_scope_violation)
            VALUES (%s, %s, %s, %s, %s);
        """, (dataset_id, username, query, response, is_violation))

        cursor.close()
        conn.close()
    except Exception as e:
        print(f"PostgreSQL chat log warning: {e}")


def get_db_statistics() -> Dict[str, Any]:
    """Provide PostgreSQL production database health and statistics metrics."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) as cnt FROM users;")
        total_users = cursor.fetchone()["cnt"]

        cursor.execute("SELECT COUNT(*) as cnt FROM datasets;")
        total_datasets = cursor.fetchone()["cnt"]

        cursor.execute("SELECT COUNT(*) as cnt FROM user_sessions;")
        active_sessions = cursor.fetchone()["cnt"]

        cursor.execute("SELECT COUNT(*) as cnt FROM chat_logs;")
        total_chats = cursor.fetchone()["cnt"]

        cursor.execute("SELECT pg_database_size(%s) as size;", (PG_DBNAME,))
        db_size_bytes = cursor.fetchone()["size"]

        cursor.execute("SELECT version();")
        version_str = cursor.fetchone()[0]

        cursor.close()
        conn.close()

        return {
            "database_type": "PostgreSQL (Enterprise Relational DB)",
            "database_host": PG_HOST,
            "database_port": PG_PORT,
            "database_user": PG_USER,
            "database_name": PG_DBNAME,
            "database_size_kb": round(db_size_bytes / 1024, 2),
            "total_registered_users": total_users,
            "total_archived_datasets": total_datasets,
            "active_sessions": active_sessions,
            "total_logged_chat_queries": total_chats,
            "version": version_str.split("on")[0].strip(),
            "status": "HEALTHY_AND_CONNECTED"
        }
    except Exception as e:
        return {
            "database_type": "PostgreSQL",
            "database_host": PG_HOST,
            "database_port": PG_PORT,
            "status": f"ERROR: {str(e)}"
        }
