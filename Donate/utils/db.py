"""
Database utility for the Donate micro-service.
Re-uses the same MySQL database as the main backend.
"""
import mysql.connector
from mysql.connector import Error
from config import Config


def get_connection():
    """Get a direct MySQL connection."""
    try:
        conn = mysql.connector.connect(
            host=Config.DB_HOST,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database=Config.DB_NAME
        )
        return conn
    except Error as e:
        print(f"[DONATE DB ERROR] {e}")
        return None


def init_payments_table():
    """Create or upgrade the payments table."""
    conn = get_connection()
    if not conn:
        print("[DONATE DB] Cannot connect — table init skipped.")
        return False

    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            id              INT AUTO_INCREMENT PRIMARY KEY,
            amount          DECIMAL(12,2) NOT NULL,
            currency        VARCHAR(10) DEFAULT 'BDT',
            method          VARCHAR(50) NOT NULL,
            status          ENUM('pending','processing','success','failed','refunded') DEFAULT 'pending',
            transaction_id  VARCHAR(255),
            gateway_ref     VARCHAR(255),
            sender_number   VARCHAR(50),
            donor_name      VARCHAR(255) DEFAULT 'Anonymous',
            donor_email     VARCHAR(255),
            is_demo         BOOLEAN DEFAULT FALSE,
            meta            JSON,
            created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_pay_status (status),
            INDEX idx_pay_method (method),
            INDEX idx_pay_trx (transaction_id),
            INDEX idx_pay_created (created_at)
        )
    """)
    conn.commit()
    cursor.close()
    conn.close()
    print("[DONATE DB] Table 'payments' ready.")
    return True
