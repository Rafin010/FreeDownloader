"""
Donate App — Production-Ready Payment Microservice
===================================================
All payment gateways (bKash, Nagad, Rocket, Stripe, PayPal)
are controlled via PAYMENT_MODE in .env (sandbox / live).

Routes:
  /donate                    → Frontend page
  /donate/api/create-payment → Start a payment
  /donate/api/verify-payment → Submit manual TrxID
  /donate/api/callback/*     → Gateway callbacks
  /donate/api/payment-config → Frontend config (keys, mode)
  /donate/api/payments/stats → Admin stats
  /donate/webhook/stripe     → Stripe webhook
  /donate/webhook/paypal     → PayPal webhook
"""
from flask import Flask, render_template, jsonify
from flask_cors import CORS
from config import Config
from utils.db import init_payments_table
from routes.payment_routes import payment_bp
from routes.webhook_routes import webhook_bp

app = Flask(__name__, static_url_path='/donate/static')
app.secret_key = Config.SECRET_KEY
CORS(app, resources={r"/donate/*": {"origins": "*"}})

# Register blueprints
app.register_blueprint(payment_bp, url_prefix='/donate/api')
app.register_blueprint(webhook_bp, url_prefix='/donate/webhook')


@app.route('/donate')
@app.route('/donate/')
@app.route('/')
def index():
    return render_template('index.html', config={
        'mode': Config.PAYMENT_MODE,
        'is_sandbox': Config.IS_SANDBOX,
    })


@app.route('/donate/health')
def health():
    return jsonify({
        'status': 'ok',
        'mode': Config.PAYMENT_MODE,
        'service': 'donate',
    })


# Initialize DB table on startup
with app.app_context():
    init_payments_table()

if __name__ == '__main__':
    print(f"[DONATE] Running in {Config.PAYMENT_MODE.upper()} mode")
    app.run(port=5007, debug=True)
