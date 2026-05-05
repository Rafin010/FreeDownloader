"""
Webhook Routes — Stripe & PayPal send server-to-server notifications here.
These verify payment completion independently of user redirects.
CRITICAL: Always verify signatures. Never trust raw POST data.
"""
from flask import Blueprint, request, jsonify
import json
from config import Config
from utils.db import get_connection
from services import stripe_pay, paypal_pay

webhook_bp = Blueprint('webhook_bp', __name__)


def _update_payment_by_ref(gateway_ref, status, trx_id=''):
    """Find and update a payment by its gateway reference."""
    conn = get_connection()
    if not conn:
        return False
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE payments SET status=%s, transaction_id=%s
            WHERE gateway_ref=%s AND status IN ('pending','processing')
        """, (status, trx_id, gateway_ref))
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        print(f"[WEBHOOK DB ERROR] {e}")
        return False
    finally:
        cursor.close()
        conn.close()


# ════════════════════════════════════════════════
#  POST /webhook/stripe
# ════════════════════════════════════════════════
@webhook_bp.route('/stripe', methods=['POST'])
def stripe_webhook():
    """
    Stripe sends checkout.session.completed here.
    We verify the signature before trusting anything.
    """
    payload = request.data
    sig = request.headers.get('Stripe-Signature', '')

    event = stripe_pay.verify_webhook(payload, sig)
    if not event:
        return jsonify({'error': 'Invalid signature'}), 400

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        session_id = session.get('id')
        payment_status = session.get('payment_status')

        if payment_status == 'paid':
            _update_payment_by_ref(session_id, 'success', trx_id=session.get('payment_intent', ''))
            print(f"[STRIPE WEBHOOK] Payment successful: {session_id}")
        else:
            _update_payment_by_ref(session_id, 'failed')
            print(f"[STRIPE WEBHOOK] Payment not paid: {session_id}")

    elif event['type'] == 'checkout.session.expired':
        session = event['data']['object']
        _update_payment_by_ref(session.get('id'), 'failed')

    return jsonify({'received': True}), 200


# ════════════════════════════════════════════════
#  POST /webhook/paypal
# ════════════════════════════════════════════════
@webhook_bp.route('/paypal', methods=['POST'])
def paypal_webhook():
    """
    PayPal sends PAYMENT.CAPTURE.COMPLETED here.
    We verify the webhook signature before trusting.
    """
    headers_dict = {
        'PAYPAL-AUTH-ALGO': request.headers.get('PAYPAL-AUTH-ALGO', ''),
        'PAYPAL-CERT-URL': request.headers.get('PAYPAL-CERT-URL', ''),
        'PAYPAL-TRANSMISSION-ID': request.headers.get('PAYPAL-TRANSMISSION-ID', ''),
        'PAYPAL-TRANSMISSION-SIG': request.headers.get('PAYPAL-TRANSMISSION-SIG', ''),
        'PAYPAL-TRANSMISSION-TIME': request.headers.get('PAYPAL-TRANSMISSION-TIME', ''),
    }

    body = request.json
    if not body:
        return jsonify({'error': 'Empty body'}), 400

    # Verify signature (skip in sandbox if needed)
    if not Config.IS_SANDBOX:
        is_valid = paypal_pay.verify_webhook(headers_dict, body)
        if not is_valid:
            return jsonify({'error': 'Invalid signature'}), 400

    event_type = body.get('event_type', '')

    if event_type == 'PAYMENT.CAPTURE.COMPLETED':
        resource = body.get('resource', {})
        capture_id = resource.get('id', '')
        # The order ID is in supplementary_data
        order_id = resource.get('supplementary_data', {}).get('related_ids', {}).get('order_id', '')

        if order_id:
            _update_payment_by_ref(order_id, 'success', trx_id=capture_id)
            print(f"[PAYPAL WEBHOOK] Payment captured: {capture_id}")

    elif event_type == 'PAYMENT.CAPTURE.DENIED':
        resource = body.get('resource', {})
        order_id = resource.get('supplementary_data', {}).get('related_ids', {}).get('order_id', '')
        if order_id:
            _update_payment_by_ref(order_id, 'failed')

    return jsonify({'received': True}), 200
