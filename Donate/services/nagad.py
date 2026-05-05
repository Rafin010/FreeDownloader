"""
Nagad Payment Service — Merchant API
Sandbox: http://sandbox.mynagad.com:10080/remote-payment-gateway-1.0/api/dfs
Live:    https://api.mynagad.com/api/dfs

Flow: Initialize → Payment URL → Callback → Verify
"""
import requests
import json
import hashlib
import datetime
from config import Config


def _generate_signature(data_str, merchant_key):
    """Simple HMAC-like signature for Nagad API."""
    return hashlib.sha256(f"{data_str}{merchant_key}".encode()).hexdigest()


def initialize_payment(amount, invoice_id, callback_url):
    """
    Step 1: Initialize checkout with Nagad.
    Returns redirect URL for user.
    """
    creds = Config.nagad()
    base = creds['base_url']
    merchant_id = creds['merchant_id']

    now = datetime.datetime.now()
    order_id = f"DON-{invoice_id}-{now.strftime('%Y%m%d%H%M%S')}"

    url = f"{base}/check-out/initialize/{merchant_id}/{order_id}"

    payload = {
        'merchantId': merchant_id,
        'orderId': order_id,
        'dateTime': now.strftime('%Y%m%d%H%M%S'),
        'amount': str(amount),
        'challenge': hashlib.md5(order_id.encode()).hexdigest(),
    }

    try:
        resp = requests.post(url, json=payload, timeout=15)
        data = resp.json()

        if data.get('callBackUrl') or data.get('sensitiveData'):
            return {
                'success': True,
                'payment_ref': data.get('paymentReferenceId', order_id),
                'redirect_url': data.get('callBackUrl', ''),
                'raw': data,
            }
        return {'success': False, 'error': data.get('reason', 'Unknown error'), 'raw': data}
    except Exception as e:
        return {'success': False, 'error': str(e)}


def verify_payment(payment_ref):
    """
    Step 2: Verify a completed payment.
    Called after Nagad callback.
    """
    creds = Config.nagad()
    base = creds['base_url']

    url = f"{base}/verify/payment/{payment_ref}"

    try:
        resp = requests.get(url, timeout=15)
        data = resp.json()
        success = data.get('status') == 'Success'
        return {
            'success': success,
            'trx_id': data.get('issuerPaymentRefNo', ''),
            'status': data.get('status', 'Unknown'),
            'raw': data,
        }
    except Exception as e:
        return {'success': False, 'error': str(e)}
