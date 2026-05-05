"""
Payment Routes — All payment creation and verification endpoints.
RULE: Never accept payment success from frontend. Always verify from backend.
"""
from flask import Blueprint, request, jsonify, redirect, url_for
import uuid
import json
from config import Config
from utils.db import get_connection
from services import bkash, nagad, rocket
from services import stripe_pay, paypal_pay

payment_bp = Blueprint('payment_bp', __name__)

BASE_URL = 'https://freedownloader.top/donate'


def _save_payment(amount, currency, method, status='pending', trx_id='', sender='', gateway_ref='', meta=None):
    """Insert a payment record and return its ID."""
    conn = get_connection()
    if not conn:
        return None
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO payments (amount, currency, method, status, transaction_id, gateway_ref, sender_number, is_demo, meta)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (amount, currency, method, status, trx_id, gateway_ref, sender, Config.IS_SANDBOX, json.dumps(meta or {})))
        conn.commit()
        pid = cursor.lastrowid
        return pid
    except Exception as e:
        print(f"[SAVE PAYMENT ERROR] {e}")
        return None
    finally:
        cursor.close()
        conn.close()


def _update_payment(payment_id, status, trx_id='', gateway_ref=''):
    """Update a payment record's status."""
    conn = get_connection()
    if not conn:
        return False
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE payments SET status=%s, transaction_id=%s, gateway_ref=%s WHERE id=%s
        """, (status, trx_id, gateway_ref, payment_id))
        conn.commit()
        return True
    except Exception as e:
        print(f"[UPDATE PAYMENT ERROR] {e}")
        return False
    finally:
        cursor.close()
        conn.close()


# ════════════════════════════════════════════════
#  POST /api/create-payment
# ════════════════════════════════════════════════
@payment_bp.route('/create-payment', methods=['POST', 'OPTIONS'])
def create_payment():
    if request.method == 'OPTIONS':
        return '', 200

    data = request.json or {}
    method = data.get('method', '').lower()
    amount = data.get('amount')
    currency = data.get('currency', 'BDT')

    if not amount or not method:
        return jsonify({'success': False, 'error': 'Amount and method are required'}), 400

    invoice_id = f"DON-{uuid.uuid4().hex[:8].upper()}"

    # ── bKash ─────────────────────────────────
    if method == 'bkash':
        callback = f"{BASE_URL}/api/callback/bkash"
        result = bkash.create_payment(amount, invoice_id, callback)
        if result['success']:
            pid = _save_payment(amount, currency, 'bkash', 'processing', gateway_ref=result.get('payment_id', ''))
            return jsonify({
                'success': True,
                'redirect_url': result['redirect_url'],
                'payment_id': pid,
                'gateway_payment_id': result.get('payment_id'),
            })
        return jsonify({'success': False, 'error': result.get('error', 'bKash create failed')}), 400

    # ── Nagad ─────────────────────────────────
    elif method == 'nagad':
        callback = f"{BASE_URL}/api/callback/nagad"
        result = nagad.initialize_payment(amount, invoice_id, callback)
        if result['success']:
            pid = _save_payment(amount, currency, 'nagad', 'processing', gateway_ref=result.get('payment_ref', ''))
            return jsonify({
                'success': True,
                'redirect_url': result.get('redirect_url', ''),
                'payment_id': pid,
            })
        return jsonify({'success': False, 'error': result.get('error', 'Nagad init failed')}), 400

    # ── Rocket (Manual) ──────────────────────
    elif method == 'rocket':
        instructions = rocket.get_payment_instructions(amount)
        pid = _save_payment(amount, currency, 'rocket', 'pending')
        instructions['payment_id'] = pid
        return jsonify(instructions)

    # ── Stripe ────────────────────────────────
    elif method == 'stripe':
        result = stripe_pay.create_checkout_session(
            amount, currency, invoice_id,
            success_url=f"{BASE_URL}/api/callback/stripe/success",
            cancel_url=f"{BASE_URL}/api/callback/stripe/cancel",
        )
        if result['success']:
            pid = _save_payment(amount, currency, 'stripe', 'processing', gateway_ref=result.get('session_id', ''))
            return jsonify({
                'success': True,
                'redirect_url': result['redirect_url'],
                'payment_id': pid,
            })
        return jsonify({'success': False, 'error': result.get('error', 'Stripe session failed')}), 400

    # ── PayPal ────────────────────────────────
    elif method == 'paypal':
        result = paypal_pay.create_order(
            amount, currency, invoice_id,
            return_url=f"{BASE_URL}/api/callback/paypal/success",
            cancel_url=f"{BASE_URL}/api/callback/paypal/cancel",
        )
        if result['success']:
            pid = _save_payment(amount, currency, 'paypal', 'processing', gateway_ref=result.get('order_id', ''))
            return jsonify({
                'success': True,
                'redirect_url': result['redirect_url'],
                'payment_id': pid,
            })
        return jsonify({'success': False, 'error': result.get('error', 'PayPal order failed')}), 400

    else:
        return jsonify({'success': False, 'error': f'Unknown method: {method}'}), 400


# ════════════════════════════════════════════════
#  POST /api/verify-payment  (Manual — Rocket/bKash/Nagad)
# ════════════════════════════════════════════════
@payment_bp.route('/verify-payment', methods=['POST', 'OPTIONS'])
def verify_payment():
    if request.method == 'OPTIONS':
        return '', 200

    data = request.json or {}
    payment_id = data.get('payment_id')
    trx_id = data.get('trx_id', '').strip()
    sender = data.get('sender', '').strip()

    if not payment_id or not trx_id:
        return jsonify({'success': False, 'error': 'payment_id and trx_id are required'}), 400

    # Store as pending — admin will verify manually
    conn = get_connection()
    if not conn:
        return jsonify({'success': False, 'error': 'DB error'}), 500

    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE payments SET status='pending', transaction_id=%s, sender_number=%s WHERE id=%s AND status IN ('pending','processing')
        """, (trx_id, sender, payment_id))
        conn.commit()
        if cursor.rowcount > 0:
            return jsonify({
                'success': True,
                'message': 'Payment submitted for verification. Thank you!',
                'payment_id': payment_id,
            })
        return jsonify({'success': False, 'error': 'Payment not found or already processed'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


# ════════════════════════════════════════════════
#  CALLBACKS (Gateway redirects back here)
# ════════════════════════════════════════════════

@payment_bp.route('/callback/bkash', methods=['GET', 'POST'])
def callback_bkash():
    """bKash redirects here after user approval."""
    payment_id = request.args.get('paymentID')
    status = request.args.get('status')

    if status == 'success' and payment_id:
        result = bkash.execute_payment(payment_id)
        if result['success']:
            # Find our DB record by gateway_ref
            conn = get_connection()
            if conn:
                cursor = conn.cursor(dictionary=True)
                cursor.execute("SELECT id FROM payments WHERE gateway_ref=%s", (payment_id,))
                row = cursor.fetchone()
                if row:
                    _update_payment(row['id'], 'success', trx_id=result.get('trx_id', ''))
                cursor.close()
                conn.close()
            return redirect(f"{BASE_URL}?status=success&trx={result.get('trx_id', '')}")
        return redirect(f"{BASE_URL}?status=failed&reason=execute_failed")

    return redirect(f"{BASE_URL}?status=failed&reason={status}")


@payment_bp.route('/callback/nagad', methods=['GET', 'POST'])
def callback_nagad():
    """Nagad redirects here after payment."""
    payment_ref = request.args.get('payment_ref_id') or request.args.get('order_id', '')

    if payment_ref:
        result = nagad.verify_payment(payment_ref)
        if result['success']:
            conn = get_connection()
            if conn:
                cursor = conn.cursor(dictionary=True)
                cursor.execute("SELECT id FROM payments WHERE gateway_ref=%s", (payment_ref,))
                row = cursor.fetchone()
                if row:
                    _update_payment(row['id'], 'success', trx_id=result.get('trx_id', ''))
                cursor.close()
                conn.close()
            return redirect(f"{BASE_URL}?status=success&trx={result.get('trx_id', '')}")

    return redirect(f"{BASE_URL}?status=failed&reason=nagad_verify_failed")


@payment_bp.route('/callback/stripe/success', methods=['GET'])
def callback_stripe_success():
    """Stripe redirects here. We do NOT trust this — webhook does the real verification."""
    return redirect(f"{BASE_URL}?status=processing&message=verifying")


@payment_bp.route('/callback/stripe/cancel', methods=['GET'])
def callback_stripe_cancel():
    return redirect(f"{BASE_URL}?status=cancelled")


@payment_bp.route('/callback/paypal/success', methods=['GET'])
def callback_paypal_success():
    """PayPal redirects here after approval. Capture the order on backend."""
    token = request.args.get('token')  # PayPal order ID
    if token:
        result = paypal_pay.capture_order(token)
        if result['success']:
            conn = get_connection()
            if conn:
                cursor = conn.cursor(dictionary=True)
                cursor.execute("SELECT id FROM payments WHERE gateway_ref=%s", (token,))
                row = cursor.fetchone()
                if row:
                    _update_payment(row['id'], 'success', trx_id=result.get('trx_id', ''))
                cursor.close()
                conn.close()
            return redirect(f"{BASE_URL}?status=success&trx={result.get('trx_id', '')}")

    return redirect(f"{BASE_URL}?status=failed&reason=paypal_capture_failed")


@payment_bp.route('/callback/paypal/cancel', methods=['GET'])
def callback_paypal_cancel():
    return redirect(f"{BASE_URL}?status=cancelled")


# ════════════════════════════════════════════════
#  GET /api/payment-config (Frontend needs this)
# ════════════════════════════════════════════════
@payment_bp.route('/payment-config', methods=['GET'])
def payment_config():
    """Return public config for frontend (publishable keys, mode, etc.)."""
    return jsonify({
        'mode': Config.PAYMENT_MODE,
        'stripe_key': stripe_pay.get_publishable_key(),
        'methods': {
            'bdt': ['bkash', 'nagad', 'rocket'],
            'usd': ['stripe', 'paypal'],
        },
    })


# ════════════════════════════════════════════════
#  GET /api/payments/stats (Admin only)
# ════════════════════════════════════════════════
@payment_bp.route('/payments/stats', methods=['GET'])
def payments_stats():
    """Aggregate payment stats for admin dashboard."""
    conn = get_connection()
    if not conn:
        return jsonify({'error': 'DB error'}), 500

    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT
                SUM(CASE WHEN currency='USD' AND status='success' THEN amount ELSE 0 END) as total_usd,
                SUM(CASE WHEN currency='BDT' AND status='success' THEN amount ELSE 0 END) as total_bdt,
                COUNT(CASE WHEN status='success' THEN 1 END) as total_success,
                COUNT(CASE WHEN status='pending' THEN 1 END) as total_pending,
                COUNT(CASE WHEN status='failed' THEN 1 END) as total_failed,
                COUNT(id) as total_all
            FROM payments
        """)
        totals = cursor.fetchone()

        cursor.execute("""
            SELECT id, amount, currency, method, status, transaction_id, sender_number,
                   is_demo, DATE_FORMAT(created_at, '%%Y-%%m-%%d %%H:%%i') as date
            FROM payments ORDER BY created_at DESC LIMIT 50
        """)
        recent = cursor.fetchall()

        return jsonify({'totals': totals, 'recent': recent})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()
