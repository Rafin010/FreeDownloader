"""
PayPal Payment Service
Sandbox: https://api-m.sandbox.paypal.com
Live:    https://api-m.paypal.com

Flow:
1. Create Order (backend)
2. Redirect user to PayPal approval page
3. User approves → PayPal redirects back
4. Capture Order (backend confirms payment)
"""
import requests
import base64
from config import Config


def _get_access_token():
    """Get OAuth2 token from PayPal."""
    creds = Config.paypal()
    url = f"{creds['base_url']}/v1/oauth2/token"
    auth = base64.b64encode(f"{creds['client_id']}:{creds['client_secret']}".encode()).decode()

    headers = {
        'Authorization': f'Basic {auth}',
        'Content-Type': 'application/x-www-form-urlencoded',
    }
    try:
        resp = requests.post(url, data='grant_type=client_credentials', headers=headers, timeout=15)
        data = resp.json()
        return data.get('access_token')
    except Exception as e:
        print(f"[PAYPAL TOKEN ERROR] {e}")
        return None


def create_order(amount, currency, invoice_id, return_url, cancel_url):
    """
    Step 1: Create a PayPal order.
    Returns approval URL for redirect.
    """
    creds = Config.paypal()
    token = _get_access_token()
    if not token:
        return {'success': False, 'error': 'Failed to get PayPal access token'}

    url = f"{creds['base_url']}/v2/checkout/orders"
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}',
    }
    payload = {
        'intent': 'CAPTURE',
        'purchase_units': [{
            'reference_id': invoice_id,
            'amount': {
                'currency_code': currency.upper(),
                'value': str(amount),
            },
            'description': f'Donation #{invoice_id} to FreeDownloader',
        }],
        'application_context': {
            'return_url': return_url,
            'cancel_url': cancel_url,
            'brand_name': 'FreeDownloader',
            'user_action': 'PAY_NOW',
        },
    }

    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=15)
        data = resp.json()

        approve_url = None
        for link in data.get('links', []):
            if link['rel'] == 'approve':
                approve_url = link['href']
                break

        return {
            'success': bool(approve_url),
            'order_id': data.get('id'),
            'redirect_url': approve_url,
            'raw': data,
        }
    except Exception as e:
        return {'success': False, 'error': str(e)}


def capture_order(order_id):
    """
    Step 2: Capture payment after user approves.
    This is called from the return_url callback.
    """
    creds = Config.paypal()
    token = _get_access_token()
    if not token:
        return {'success': False, 'error': 'Failed to get PayPal access token'}

    url = f"{creds['base_url']}/v2/checkout/orders/{order_id}/capture"
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}',
    }

    try:
        resp = requests.post(url, headers=headers, timeout=15)
        data = resp.json()
        success = data.get('status') == 'COMPLETED'

        trx_id = ''
        captures = data.get('purchase_units', [{}])[0].get('payments', {}).get('captures', [])
        if captures:
            trx_id = captures[0].get('id', '')

        return {
            'success': success,
            'trx_id': trx_id,
            'status': data.get('status'),
            'raw': data,
        }
    except Exception as e:
        return {'success': False, 'error': str(e)}


def verify_webhook(headers_dict, body):
    """
    Verify PayPal webhook signature.
    In production, use PayPal's verification endpoint.
    """
    creds = Config.paypal()
    token = _get_access_token()
    if not token:
        return None

    url = f"{creds['base_url']}/v1/notifications/verify-webhook-signature"
    verify_payload = {
        'auth_algo': headers_dict.get('PAYPAL-AUTH-ALGO', ''),
        'cert_url': headers_dict.get('PAYPAL-CERT-URL', ''),
        'transmission_id': headers_dict.get('PAYPAL-TRANSMISSION-ID', ''),
        'transmission_sig': headers_dict.get('PAYPAL-TRANSMISSION-SIG', ''),
        'transmission_time': headers_dict.get('PAYPAL-TRANSMISSION-TIME', ''),
        'webhook_id': 'YOUR_WEBHOOK_ID',  # Set this in .env later
        'webhook_event': body,
    }

    try:
        resp = requests.post(url, json=verify_payload,
                             headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'},
                             timeout=15)
        data = resp.json()
        return data.get('verification_status') == 'SUCCESS'
    except Exception as e:
        print(f"[PAYPAL WEBHOOK VERIFY ERROR] {e}")
        return False
