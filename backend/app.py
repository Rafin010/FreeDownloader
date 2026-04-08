from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_cors import CORS
from functools import wraps
from dotenv import load_dotenv
from utils.db import initialize_database
from routes.analytics_routes import analytics_bp
from routes.dashboard_routes import dashboard_bp
import os
import secrets

# Load .env BEFORE accessing any env vars
load_dotenv()

# ── Hardcoded admin credentials ──
ADMIN_EMAIL    = "admin@freedownloader.top"
ADMIN_PASSWORD = "@freedownloader"

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY") or secrets.token_hex(32)

# Allow all origins (tighten in production)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Register blueprints
app.register_blueprint(analytics_bp,  url_prefix="/api")
app.register_blueprint(dashboard_bp,  url_prefix="/api/dashboard")


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

        if email == ADMIN_EMAIL and password == ADMIN_PASSWORD:
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
