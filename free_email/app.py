from flask import Flask, redirect, url_for, session, request, jsonify, render_template
from authlib.integrations.flask_client import OAuth
from email.mime.text import MIMEText
from googleapiclient.discovery import build
import base64
import time

app = Flask(__name__)
app.secret_key = "SUPER_SECRET_KEY_CHANGE_IT"

# Session fix
app.config['SESSION_COOKIE_NAME'] = 'google-login-session'

# ==============================
# 🔐 Google OAuth Setup
# ==============================
oauth = OAuth(app)

google = oauth.register(
    name='google',
    client_id="938781722162-90bqak8phjbfigh4o539jcp7clugqjfb.apps.googleusercontent.com",
    client_secret="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",
    access_token_url='https://oauth2.googleapis.com/token',
    authorize_url='https://accounts.google.com/o/oauth2/auth',
    api_base_url='https://www.googleapis.com/oauth2/v1/',
    client_kwargs={
        'scope': 'openid email profile https://www.googleapis.com/auth/gmail.send'
    }
)

"""
938781722162-90bqak8phjbfigh4o539jcp7clugqjfb.apps.googleusercontent.com
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
"""

# ==============================
# 🏠 Home Route
# ==============================
@app.route('/')
def home():
    return render_template('index.html')

# ==============================
# 🔑 Login Route
# ==============================
@app.route('/login')
def login():
    return google.authorize_redirect(url_for('callback', _external=True))


# ==============================
# 🔁 Callback Route
# ==============================
@app.route('/callback')
def callback():
    token = google.authorize_access_token()
    resp = google.get('userinfo')
    user_info = resp.json()

    session['user'] = user_info
    session['token'] = token

    return redirect("http://localhost:5000")  # frontend URL


# ==============================
# 👤 Get User Info
# ==============================
@app.route('/get-user')
def get_user():
    if 'user' in session:
        return jsonify({
            "logged_in": True,
            "email": session['user']['email']
        })
    return jsonify({"logged_in": False})


# ==============================
# 📩 Send Single Email
# ==============================
def send_single_email(service, recipient, subject, message):
    msg = MIMEText(message, 'html')
    msg['to'] = recipient
    msg['subject'] = subject

    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()

    return service.users().messages().send(
        userId="me",
        body={'raw': raw}
    ).execute()


# ==============================
# 🚀 Bulk Email API (Optimized)
# ==============================
@app.route('/send-bulk-email', methods=['POST'])
def send_bulk_email():
    if 'token' not in session:
        return jsonify({"success": False, "error": "Not authenticated"})

    data = request.json
    emails = data.get('emails', [])
    subject = data.get('subject')
    message = data.get('message')

    credentials = session['token']
    service = build('gmail', 'v1', credentials=credentials)

    success = 0
    failed = 0
    results = []

    #  Rate limit safe config
    BATCH_SIZE = 10       
    DELAY = 2             

    for i, email in enumerate(emails):
        try:
            send_single_email(service, email, subject, message)
            success += 1
            results.append({"email": email, "status": "sent"})
            print(f"[SUCCESS] {email}")

        except Exception as e:
            failed += 1
            results.append({"email": email, "status": "failed", "error": str(e)})
            print(f"[FAILED] {email} - {e}")

        # 🔐 Rate limit protection
        if (i + 1) % BATCH_SIZE == 0:
            print("⏳ Cooling down...")
            time.sleep(DELAY)

    return jsonify({
        "success": True,
        "total": len(emails),
        "sent": success,
        "failed": failed,
        "details": results
    })


# ==============================
# Logout
# ==============================
@app.route('/logout')
def logout():
    session.clear()
    return redirect("/")


# ==============================
# ▶ Run App
# ==============================                    ----------------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True)