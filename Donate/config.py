"""
Config Module — Loads environment variables and resolves sandbox vs live credentials.
Switch PAYMENT_MODE in .env to toggle between sandbox and live.
"""
import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))


class Config:
    PAYMENT_MODE = os.getenv('PAYMENT_MODE', 'sandbox')  # 'sandbox' or 'live'
    IS_SANDBOX = PAYMENT_MODE == 'sandbox'

    SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'change_me')

    # ── Database ──────────────────────────────────────────
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_USER = os.getenv('DB_USER', 'root')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')
    DB_NAME = os.getenv('DB_NAME', 'downloader_analytics')

    # ── bKash ─────────────────────────────────────────────
    @staticmethod
    def bkash():
        mode = 'SANDBOX' if Config.IS_SANDBOX else 'LIVE'
        return {
            'app_key': os.getenv(f'BKASH_{mode}_APP_KEY', ''),
            'app_secret': os.getenv(f'BKASH_{mode}_APP_SECRET', ''),
            'username': os.getenv(f'BKASH_{mode}_USERNAME', ''),
            'password': os.getenv(f'BKASH_{mode}_PASSWORD', ''),
            'base_url': os.getenv(f'BKASH_{mode}_BASE_URL', ''),
        }

    # ── Nagad ─────────────────────────────────────────────
    @staticmethod
    def nagad():
        mode = 'SANDBOX' if Config.IS_SANDBOX else 'LIVE'
        return {
            'merchant_id': os.getenv(f'NAGAD_{mode}_MERCHANT_ID', ''),
            'merchant_key': os.getenv(f'NAGAD_{mode}_MERCHANT_KEY', ''),
            'base_url': os.getenv(f'NAGAD_{mode}_BASE_URL', ''),
        }

    # ── Rocket ────────────────────────────────────────────
    @staticmethod
    def rocket():
        return {
            'admin_number': os.getenv('ROCKET_ADMIN_NUMBER', '017XXXXXXXX'),
        }

    # ── Stripe ────────────────────────────────────────────
    @staticmethod
    def stripe():
        mode = 'SANDBOX' if Config.IS_SANDBOX else 'LIVE'
        return {
            'secret_key': os.getenv(f'STRIPE_{mode}_SECRET_KEY', ''),
            'publishable_key': os.getenv(f'STRIPE_{mode}_PUBLISHABLE_KEY', ''),
            'webhook_secret': os.getenv(f'STRIPE_{mode}_WEBHOOK_SECRET', ''),
        }

    # ── PayPal ────────────────────────────────────────────
    @staticmethod
    def paypal():
        mode = 'SANDBOX' if Config.IS_SANDBOX else 'LIVE'
        return {
            'client_id': os.getenv(f'PAYPAL_{mode}_CLIENT_ID', ''),
            'client_secret': os.getenv(f'PAYPAL_{mode}_CLIENT_SECRET', ''),
            'base_url': os.getenv(f'PAYPAL_{mode}_BASE_URL', ''),
        }
