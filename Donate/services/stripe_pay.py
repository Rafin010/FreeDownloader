"""
Stripe Payment Service
Test Mode:  sk_test_... / pk_test_...
Live Mode:  sk_live_... / pk_live_...

Flow:
1. Create Checkout Session (backend)
2. Redirect user to Stripe hosted page
3. Stripe sends webhook on completion
4. Backend verifies webhook signature → updates DB
"""
import json
from config import Config

try:
    import stripe
except ImportError:
    stripe = None
    print("[STRIPE] stripe library not installed. Run: pip install stripe")


def _init_stripe():
    """Set the correct API key based on payment mode."""
    if stripe is None:
        return False
    creds = Config.stripe()
    stripe.api_key = creds['secret_key']
    return True


def create_checkout_session(amount, currency, invoice_id, success_url, cancel_url):
    """
    Create a Stripe Checkout Session.
    Returns session URL for redirect.
    """
    if not _init_stripe():
        return {'success': False, 'error': 'Stripe SDK not available'}

    try:
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': currency.lower(),
                    'product_data': {
                        'name': 'Donation to FreeDownloader',
                        'description': f'Donation #{invoice_id}',
                    },
                    'unit_amount': int(float(amount) * 100),  # Stripe uses cents
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=success_url + '?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=cancel_url,
            metadata={
                'invoice_id': invoice_id,
                'is_demo': str(Config.IS_SANDBOX),
            },
        )
        return {
            'success': True,
            'session_id': session.id,
            'redirect_url': session.url,
        }
    except Exception as e:
        return {'success': False, 'error': str(e)}


def verify_webhook(payload, sig_header):
    """
    Verify Stripe webhook signature. NEVER trust frontend.
    Returns parsed event or None.
    """
    if not _init_stripe():
        return None

    creds = Config.stripe()
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, creds['webhook_secret']
        )
        return event
    except stripe.error.SignatureVerificationError:
        print("[STRIPE WEBHOOK] Signature verification failed!")
        return None
    except Exception as e:
        print(f"[STRIPE WEBHOOK ERROR] {e}")
        return None


def get_publishable_key():
    """Return the publishable key for frontend."""
    creds = Config.stripe()
    return creds['publishable_key']
