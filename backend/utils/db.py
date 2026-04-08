import mysql.connector
from mysql.connector import Error, pooling
from dotenv import load_dotenv
import os

load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "downloader_analytics")

# ── Connection Pool ───────────────────────────────────────────
_pool = None


def _get_pool():
    """Lazy-init a connection pool (5 connections by default)."""
    global _pool
    if _pool is None:
        try:
            _pool = pooling.MySQLConnectionPool(
                pool_name="fdl_pool",
                pool_size=5,
                pool_reset_session=True,
                host=DB_HOST,
                user=DB_USER,
                password=DB_PASSWORD,
                database=DB_NAME
            )
        except Error as e:
            print(f"[DB POOL ERROR] {e}")
            return None
    return _pool


def get_connection(use_db=True):
    """Get a connection — from pool if available, else direct."""
    try:
        if use_db:
            pool = _get_pool()
            if pool:
                return pool.get_connection()
        # Fallback for use_db=False (database creation) or pool failure
        params = dict(host=DB_HOST, user=DB_USER, password=DB_PASSWORD)
        if use_db:
            params["database"] = DB_NAME
        connection = mysql.connector.connect(**params)
        return connection
    except Error as e:
        print(f"[DB ERROR] {e}")
        return None


# ── Default websites to auto-register ─────────────────────────────
DEFAULT_SITES = [
    {"name": "YouTube Downloader",    "url": "yt_downloader"},
    {"name": "Facebook Downloader",   "url": "fb_downloader"},
    {"name": "Instagram Downloader",  "url": "insta_downloader"},
    {"name": "TikTok Downloader",     "url": "tiktok_downloader"},
    {"name": "Free Downloader",       "url": "free_downloader"},
]


def initialize_database():
    print("=" * 50)
    print("  Initializing Database...")
    print("=" * 50)

    # Step 1 — connect without DB to create it
    conn = get_connection(use_db=False)
    if not conn:
        print("[FATAL] Cannot connect to MySQL.")
        print("  -> Make sure XAMPP / MySQL is running!")
        print("  -> Check DB_HOST, DB_USER, DB_PASSWORD in .env")
        return False

    cursor = conn.cursor()
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}`")
    print(f"  [OK] Database '{DB_NAME}' ready.")
    cursor.close()
    conn.close()

    # Step 2 — connect to DB and create tables
    conn = get_connection()
    if not conn:
        print("[FATAL] Cannot connect to database after creation.")
        return False
    cursor = conn.cursor()

    # ── websites ──────────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS websites (
            id   INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            url  VARCHAR(255) NOT NULL UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("  [OK] Table 'websites' ready.")

    # ── sessions ──────────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id          INT AUTO_INCREMENT PRIMARY KEY,
            session_id  VARCHAR(255) UNIQUE NOT NULL,
            website_id  VARCHAR(255) NOT NULL,
            ip_address  VARCHAR(45),
            country     VARCHAR(100),
            city        VARCHAR(100),
            device_type VARCHAR(100),
            category    VARCHAR(100) DEFAULT 'general',
            cookie_id   VARCHAR(255),
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_session (session_id),
            INDEX idx_website (website_id),
            INDEX idx_cookie (cookie_id)
        )
    """)
    print("  [OK] Table 'sessions' ready.")

    # ── events ────────────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id          INT AUTO_INCREMENT PRIMARY KEY,
            session_id  VARCHAR(255) NOT NULL,
            website_id  VARCHAR(255) NOT NULL,
            event_type  VARCHAR(50)  NOT NULL,
            category    VARCHAR(100),
            cookie_id   VARCHAR(255),
            meta        TEXT,
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE,
            INDEX idx_ev_website (website_id),
            INDEX idx_ev_type (event_type),
            INDEX idx_ev_date (created_at),
            INDEX idx_ev_cookie (cookie_id)
        )
    """)
    print("  [OK] Table 'events' ready.")

    # ── active_users ──────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS active_users (
            id         INT AUTO_INCREMENT PRIMARY KEY,
            session_id VARCHAR(255) UNIQUE NOT NULL,
            website_id VARCHAR(255) NOT NULL,
            last_ping  TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE,
            INDEX idx_au_website (website_id),
            INDEX idx_au_ping (last_ping)
        )
    """)
    print("  [OK] Table 'active_users' ready.")

    # ── user_cookies (NEW — for cookie-based tracking) ────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_cookies (
            id          INT AUTO_INCREMENT PRIMARY KEY,
            cookie_id   VARCHAR(255) UNIQUE NOT NULL,
            preferences JSON,
            total_views     INT DEFAULT 0,
            total_downloads INT DEFAULT 0,
            first_seen  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_seen   TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_uc_cookie (cookie_id),
            INDEX idx_uc_last_seen (last_seen)
        )
    """)
    print("  [OK] Table 'user_cookies' ready.")

    # ── Seed default websites ─────────────────────────────────────
    for site in DEFAULT_SITES:
        try:
            cursor.execute(
                "INSERT IGNORE INTO websites (name, url) VALUES (%s, %s)",
                (site["name"], site["url"])
            )
        except Exception:
            pass  # already exists, skip

    conn.commit()
    cursor.close()
    conn.close()

    # Reset pool so it connects to the now-initialized DB
    global _pool
    _pool = None

    print("=" * 50)
    print("  Database Initialized Successfully!")
    print(f"  Registered {len(DEFAULT_SITES)} default websites.")
    print("=" * 50)
    return True


if __name__ == "__main__":
    initialize_database()
