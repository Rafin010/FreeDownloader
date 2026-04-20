from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_cors import CORS
from functools import wraps
from dotenv import load_dotenv
from utils.db import initialize_database
from routes.analytics_routes import analytics_bp
from routes.dashboard_routes import dashboard_bp
from apscheduler.schedulers.background import BackgroundScheduler
import os
import secrets
import time
import bcrypt

# Load .env BEFORE accessing any env vars
load_dotenv()

# ── Admin credentials from environment (NEVER hardcode in production) ──
ADMIN_EMAIL         = os.getenv("ADMIN_EMAIL", "admin@freedownloader.top")
ADMIN_PASSWORD      = os.getenv("ADMIN_PASSWORD", "@freedownloader")
ADMIN_PASSWORD_HASH = os.getenv("ADMIN_PASSWORD_HASH")

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY") or secrets.token_hex(32)

# Restrict CORS to actual domains in production
CORS(app, resources={r"/api/*": {"origins": [
    "https://freedownloader.top",
    "https://www.freedownloader.top",
    "https://admin.freedownloader.top",
    "https://youtube.freedownloader.top",
    "https://tiktok.freedownloader.top",
    "https://instagram.freedownloader.top",
    "https://facebook.freedownloader.top",
    "https://porn.freedownloader.top",
    "http://localhost:5000"
]}})

# Register blueprints
app.register_blueprint(analytics_bp,  url_prefix="/api")
app.register_blueprint(dashboard_bp,  url_prefix="/api/dashboard")

try:
    from routes.store_routes import store_bp
    app.register_blueprint(store_bp, url_prefix="/api/store")
except ImportError:
    pass

try:
    from routes.popup_routes import popup_bp
    app.register_blueprint(popup_bp, url_prefix="/api/popup")
except ImportError:
    pass

try:
    from routes.install_routes import install_bp
    app.register_blueprint(install_bp, url_prefix="/api/install")
except ImportError:
    pass

# File upload config
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'freeStore', 'uploads')
os.makedirs(os.path.join(UPLOAD_FOLDER, 'web'), exist_ok=True)
os.makedirs(os.path.join(UPLOAD_FOLDER, 'app'), exist_ok=True)
os.makedirs(os.path.join(UPLOAD_FOLDER, 'software'), exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500 MB max

# Background task for stale install cleanup
def cleanup_stale_installs():
    from utils.db import get_connection
    conn = get_connection()
    if conn:
        cursor = conn.cursor()
        try:
            cursor.execute("""
                UPDATE software_installs
                SET is_active = FALSE, uninstalled_at = CURRENT_TIMESTAMP
                WHERE is_active = TRUE AND last_heartbeat < NOW() - INTERVAL 15 MINUTE
            """)
            conn.commit()
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Cleanup stale installs: OK")
        except Exception as e:
            conn.rollback()
            print(f"[CLEANUP ERROR] {e}")
        finally:
            cursor.close()
            conn.close()

scheduler = BackgroundScheduler(daemon=True)
scheduler.add_job(func=cleanup_stale_installs, trigger="interval", minutes=5)
scheduler.start()


# ── Auth helper ──
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


@app.route("/")
@login_required
def dashboard():
    return render_template("dashboard.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("logged_in"):
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        email    = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        is_valid = False
        if email == ADMIN_EMAIL:
            if ADMIN_PASSWORD_HASH:
                is_valid = bcrypt.checkpw(password.encode('utf-8'), ADMIN_PASSWORD_HASH.encode('utf-8'))
            else:
                is_valid = (password == ADMIN_PASSWORD)

        if is_valid:
            session["logged_in"] = True
            session["user"]      = email
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid email or password.", "error")
            return redirect(url_for("login"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    initialize_database()
    app.run(debug=True, host="0.0.0.0", port=5000)
