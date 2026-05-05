"""
bKash Payment Service — Tokenized Checkout API
Sandbox: https://tokenized.sandbox.bka.sh/v1.2.0-beta
Live:    https://tokenized.pay.bka.sh/v1.2.0-beta

Flow: Grant Token → Create Payment → (User Approves) → Execute Payment
"""
import requests
import json
from config import Config

_token_cache = {'token': None, 'refresh': None}


def _grant_token():
    """Step 1: Get auth token from bKash."""
    creds = Config.bkash()
    url = f"{creds['base_url']}/tokenized/checkout/token/grant"
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'username': creds['username'],
        'password': creds['password'],
    }
    payload = {
        'app_key': creds['app_key'],
        'app_secret': creds['app_secret'],
    }
    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=15)
        data = resp.json()
        if data.get('id_token'):
            _token_cache['token'] = data['id_token']
            _token_cache['refresh'] = data.get('refresh_token')
            return data['id_token']
        print(f"[BKASH TOKEN ERROR] {data}")
        return None
    except Exception as e:
        print(f"[BKASH TOKEN EXCEPTION] {e}")
        return None


def _get_headers():
    """Build authorized headers."""
    creds = Config.bkash()
    token = _token_cache.get('token') or _grant_token()
    return {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Authorization': token or '',
        'X-APP-Key': creds['app_key'],
    }


def create_payment(amount, invoice_id, callback_url):
    """
    Step 2: Create a payment request.
    Returns: { paymentID, bkashURL, ... } or error dict.
    """
    creds = Config.bkash()
    url = f"{creds['base_url']}/tokenized/checkout/create"
    payload = {
        'mode': '0011',
        'payerReference': ' ',
        'callbackURL': callback_url,
        'amount': str(amount),
        'currency': 'BDT',
        'intent': 'sale',
        'merchantInvoiceNumber': invoice_id,
    }
    try:
        resp = requests.post(url, json=payload, headers=_get_headers(), timeout=15)
        data = resp.json()
        return {
            'success': bool(data.get('bkashURL')),
            'payment_id': data.get('paymentID'),
            'redirect_url': data.get('bkashURL'),
            'raw': data,
        }
    except Exception as e:
        return {'success': False, 'error': str(e)}


def execute_payment(payment_id):
    """
    Step 3: Execute after user approves on bKash side.
    Returns: { trxID, transactionStatus, ... } or error.
    """
    creds = Config.bkash()
    url = f"{creds['base_url']}/tokenized/checkout/execute"
    payload = {'paymentID': payment_id}
    try:
        resp = requests.post(url, json=payload, headers=_get_headers(), timeout=15)
        data = resp.json()
        success = data.get('transactionStatus') == 'Completed'
        return {
            'success': success,
            'trx_id': data.get('trxID'),
            'status': data.get('transactionStatus'),
            'raw': data,
        }
    except Exception as e:
        return {'success': False, 'error': str(e)}


def query_payment(payment_id):
    """Optional: Query payment status."""
    creds = Config.bkash()
    url = f"{creds['base_url']}/tokenized/checkout/payment/status"
    payload = {'paymentID': payment_id}
    try:
        resp = requests.post(url, json=payload, headers=_get_headers(), timeout=15)
        return resp.json()
    except Exception as e:
        return {'error': str(e)}
