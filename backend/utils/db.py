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
    {"name": "Porn Downloader",       "url": "porn_downloader"},
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

    # ── store_items (Free Store catalog) ──────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS store_items (
            id                INT AUTO_INCREMENT PRIMARY KEY,
            title             VARCHAR(255) NOT NULL,
            slug              VARCHAR(255) UNIQUE NOT NULL,
            category          VARCHAR(50) NOT NULL DEFAULT 'software',
            developer         VARCHAR(255) DEFAULT 'Ifat Ahmed Rafin',
            description       TEXT,
            long_description  TEXT,
            version           VARCHAR(50) DEFAULT '1.0.0',
            rating            DECIMAL(2,1) DEFAULT 0.0,
            price             VARCHAR(50) DEFAULT 'Free',
            download_link     VARCHAR(500),
            file_path         VARCHAR(500),
            file_size         VARCHAR(50),
            icon_url          VARCHAR(500),
            screenshots       JSON,
            system_requirements JSON,
            is_active         BOOLEAN DEFAULT TRUE,
            download_count    INT DEFAULT 0,
            created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_si_category (category),
            INDEX idx_si_slug (slug),
            INDEX idx_si_active (is_active)
        )
    """)
    print("  [OK] Table 'store_items' ready.")

    # ── popup_campaigns (Remote in-app popups) ────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS popup_campaigns (
            id                  INT AUTO_INCREMENT PRIMARY KEY,
            title               VARCHAR(255) NOT NULL,
            message             TEXT NOT NULL,
            popup_type          VARCHAR(50) DEFAULT 'donation',
            button_text         VARCHAR(100) DEFAULT 'Donate Now',
            button_url          VARCHAR(500),
            category_filter     VARCHAR(100),
            schedule_type       VARCHAR(50) DEFAULT 'always',
            schedule_dates      JSON,
            schedule_interval_days INT,
            is_active           BOOLEAN DEFAULT TRUE,
            priority            INT DEFAULT 0,
            shown_count         INT DEFAULT 0,
            click_count         INT DEFAULT 0,
            start_date          DATETIME,
            end_date            DATETIME,
            created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_pc_active (is_active),
            INDEX idx_pc_type (popup_type)
        )
    """)
    print("  [OK] Table 'popup_campaigns' ready.")

    # ── popup_interactions ────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS popup_interactions (
            id              INT AUTO_INCREMENT PRIMARY KEY,
            campaign_id     INT NOT NULL,
            user_id         VARCHAR(255) NOT NULL,
            action          VARCHAR(50) NOT NULL,
            created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (campaign_id) REFERENCES popup_campaigns(id) ON DELETE CASCADE,
            INDEX idx_pi_campaign (campaign_id),
            INDEX idx_pi_user (user_id)
        )
    """)
    print("  [OK] Table 'popup_interactions' ready.")

    # ── donations ─────────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS donations (
            id              INT AUTO_INCREMENT PRIMARY KEY,
            user_id         VARCHAR(255),
            campaign_id     INT,
            amount          DECIMAL(10,2) NOT NULL,
            currency        VARCHAR(10) DEFAULT 'USD',
            payment_status  VARCHAR(50) DEFAULT 'pending',
            payment_method  VARCHAR(50),
            transaction_id  VARCHAR(255),
            donor_name      VARCHAR(255),
            donor_email     VARCHAR(255),
            created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (campaign_id) REFERENCES popup_campaigns(id) ON DELETE SET NULL,
            INDEX idx_don_status (payment_status),
            INDEX idx_don_user (user_id)
        )
    """)
    print("  [OK] Table 'donations' ready.")

    # ── software_installs (Active user tracking) ──────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS software_installs (
            id              INT AUTO_INCREMENT PRIMARY KEY,
            install_id      VARCHAR(255) UNIQUE NOT NULL,
            user_id         VARCHAR(255) NOT NULL,
            software_id     INT,
            software_name   VARCHAR(255),
            app_version     VARCHAR(50),
            os_type         VARCHAR(50),
            os_version      VARCHAR(100),
            device_id       VARCHAR(255),
            is_active       BOOLEAN DEFAULT TRUE,
            last_heartbeat  TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            installed_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            uninstalled_at  TIMESTAMP NULL,
            FOREIGN KEY (software_id) REFERENCES store_items(id) ON DELETE SET NULL,
            INDEX idx_swi_active (is_active),
            INDEX idx_swi_software (software_id),
            INDEX idx_swi_heartbeat (last_heartbeat),
            INDEX idx_swi_user (user_id)
        )
    """)
    print("  [OK] Table 'software_installs' ready.")

    # ── Seed default websites ─────────────────────────────────────
    for site in DEFAULT_SITES:
        try:
            cursor.execute(
                "INSERT IGNORE INTO websites (name, url) VALUES (%s, %s)",
                (site["name"], site["url"])
            )
        except Exception:
            pass  # already exists, skip

    # ── Seed default store items ──────────────────────────────────
    DEFAULT_STORE_ITEMS = [
        {
            "title": "SportyXi Lite",
            "slug": "sportyxi-lite",
            "category": "app",
            "description": "লাইভ স্পোর্টস স্ট্রিমিং এবং রিয়েল-টাইম স্কোর আপডেটের জন্য একটি প্রফেশনাল প্ল্যাটফর্ম।",
            "long_description": "SportyXi Lite is a professional live sports streaming platform offering real-time score updates, match highlights, and multi-sport coverage. Stay connected to your favorite games with HD streaming quality and minimal latency. Features include personalized notifications, match schedules, and comprehensive statistics.",
            "version": "1.2.0",
            "rating": "4.8",
            "price": "Free",
            "download_link": "#download_app"
        },
        {
            "title": "Free Downloader",
            "slug": "free-downloader",
            "category": "software",
            "description": "যেকোনো প্ল্যাটফর্ম থেকে এক ক্লিকে হাই-কোয়ালিটি ভিডিও ডাউনলোড করার ফাস্ট এবং সিকিউর সফটওয়্যার।",
            "long_description": "Free Downloader is a fast, secure, and reliable software for downloading high-quality videos from any platform with just one click. Supports YouTube, Facebook, Instagram, TikTok, and 100+ websites. Features batch downloading, format selection (MP4, MP3, WebM), quality options up to 4K, and a built-in media player.",
            "version": "2.0.1",
            "rating": "4.5",
            "price": "Free",
            "download_link": "#download_software"
        },
        {
            "title": "Neon Dashboard",
            "slug": "neon-dashboard",
            "category": "web",
            "description": "অ্যাডমিন প্যানেলের জন্য মডার্ন গ্লাসমরফিজম এবং ডার্ক থিম ড্যাশবোর্ড টেমপ্লেট।",
            "long_description": "Neon Dashboard is a modern, glassmorphic dark-themed admin panel template designed for web applications. Features responsive layouts, interactive charts, real-time data widgets, and a comprehensive component library. Built with clean, modular code for easy customization and integration.",
            "version": "1.0.0",
            "rating": "5.0",
            "price": "Free",
            "download_link": "https://www.google.com"
        }
    ]
    for item in DEFAULT_STORE_ITEMS:
        try:
            cursor.execute("""
                INSERT IGNORE INTO store_items
                (title, slug, category, description, long_description, version, rating, price, download_link)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                item["title"], item["slug"], item["category"],
                item["description"], item["long_description"],
                item["version"], item["rating"], item["price"],
                item["download_link"]
            ))
        except Exception:
            pass

    conn.commit()
    cursor.close()
    conn.close()

    # Reset pool so it connects to the now-initialized DB
    global _pool
    _pool = None

    print("=" * 50)
    print("  Database Initialized Successfully!")
    print(f"  Registered {len(DEFAULT_SITES)} default websites.")
    print(f"  Seeded {len(DEFAULT_STORE_ITEMS)} default store items.")
    print("=" * 50)
    return True


if __name__ == "__main__":
    initialize_database()
