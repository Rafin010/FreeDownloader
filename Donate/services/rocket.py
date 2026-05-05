"""
Rocket Payment Service — Manual Verification System
Rocket (DBBL) does not have a public merchant API.
This service handles manual send-money verification.

Flow:
1. User sends money to admin number
2. User submits sender number + TrxID
3. Backend stores as 'pending' for admin verification
4. Admin verifies via dashboard and marks as success/failed
"""
from config import Config


def get_payment_instructions(amount):
    """
    Return instructions for the user to make a manual Rocket payment.
    """
    creds = Config.rocket()
    return {
        'success': True,
        'method': 'rocket',
        'admin_number': creds['admin_number'],
        'amount': amount,
        'instructions': [
            f"Open your Rocket app or dial *322#",
            f"Select 'Send Money'",
            f"Enter number: {creds['admin_number']}",
            f"Enter amount: ৳{amount}",
            f"Enter your Rocket PIN",
            f"Note the Transaction ID (TrxID)",
            f"Come back and enter your TrxID to verify",
        ],
    }


def submit_verification(sender_number, trx_id, amount):
    """
    Record a pending manual verification.
    Admin will verify this from dashboard later.
    Returns a dict to be stored in DB.
    """
    return {
        'success': True,
        'status': 'pending',
        'sender_number': sender_number,
        'trx_id': trx_id,
        'amount': amount,
        'message': 'Payment submitted for manual verification. You will be notified once confirmed.',
    }
