from flask import Blueprint, request, jsonify
from utils.db import get_connection
import json

analytics_bp = Blueprint('analytics', __name__)


# ─────────────────────────────────────────────
# POST /api/ping   — heartbeat / active-user keep-alive
# ─────────────────────────────────────────────
@analytics_bp.route('/ping', methods=['POST'])
def ping():
    data = request.get_json(silent=True) or {}
    session_id = data.get('session_id', '').strip()
    website_id = data.get('website_id', '').strip()

    if not session_id or not website_id:
        return jsonify({"error": "Missing session_id or website_id"}), 400

    conn = get_connection()
    if not conn:
        return jsonify({"error": "Database unavailable"}), 500

    cursor = conn.cursor()

    # Ensure session row exists (in case ping arrives before first event)
    ip = request.remote_addr
    ua = request.headers.get('User-Agent', '')
    cursor.execute("""
        INSERT IGNORE INTO sessions (session_id, website_id, ip_address, device_type)
        VALUES (%s, %s, %s, %s)
    """, (session_id, website_id, ip, ua))

    cursor.execute("""
        INSERT INTO active_users (session_id, website_id, last_ping)
        VALUES (%s, %s, CURRENT_TIMESTAMP)
        ON DUPLICATE KEY UPDATE last_ping = CURRENT_TIMESTAMP
    """, (session_id, website_id))

    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"status": "ok"})


# ─────────────────────────────────────────────
# POST /api/event  — track page_view | download | ad_impression
# ─────────────────────────────────────────────
@analytics_bp.route('/event', methods=['POST'])
def track_event():
    data = request.get_json(silent=True) or {}
    session_id  = data.get('session_id', '').strip()
    website_id  = data.get('website_id', '').strip()
    event_type  = data.get('event_type', '').strip()   # page_view | download | ad_impression
    category    = data.get('category', 'general')
    meta        = data.get('meta')   # optional dict for extra info

    if not session_id or not website_id or not event_type:
        return jsonify({"error": "Missing required fields"}), 400

    if event_type not in ('page_view', 'download', 'ad_impression'):
        return jsonify({"error": "Invalid event_type"}), 400

    ip = request.remote_addr
    ua = request.headers.get('User-Agent', '')
    meta_json = json.dumps(meta) if meta else None

    conn = get_connection()
    if not conn:
        return jsonify({"error": "Database unavailable"}), 500

    cursor = conn.cursor()

    # Upsert session
    cursor.execute("""
        INSERT IGNORE INTO sessions (session_id, website_id, ip_address, device_type, category)
        VALUES (%s, %s, %s, %s, %s)
    """, (session_id, website_id, ip, ua, category))

    cursor.execute("""
        UPDATE sessions SET last_active = CURRENT_TIMESTAMP WHERE session_id = %s
    """, (session_id,))

    # Insert event
    cursor.execute("""
        INSERT INTO events (session_id, website_id, event_type, category, meta)
        VALUES (%s, %s, %s, %s, %s)
    """, (session_id, website_id, event_type, category, meta_json))

    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"status": "ok"})


# ─────────────────────────────────────────────
# GET /api/sites   — list all registered websites
# ─────────────────────────────────────────────
@analytics_bp.route('/sites', methods=['GET'])
def list_sites():
    conn = get_connection()
    if not conn:
        return jsonify({"error": "Database unavailable"}), 500

    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, name, url, created_at FROM websites ORDER BY created_at DESC")
    sites = cursor.fetchall()
    cursor.close()
    conn.close()
    # Convert datetime to string
    for s in sites:
        if s.get('created_at'):
            s['created_at'] = str(s['created_at'])
    return jsonify(sites)


# ─────────────────────────────────────────────
# POST /api/register-site   — register a new site
# ─────────────────────────────────────────────
@analytics_bp.route('/register-site', methods=['POST'])
def register_site():
    data = request.get_json(silent=True) or {}
    name = data.get('name', '').strip()
    url  = data.get('url', '').strip()

    if not name or not url:
        return jsonify({"error": "name and url are required"}), 400

    conn = get_connection()
    if not conn:
        return jsonify({"error": "Database unavailable"}), 500

    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO websites (name, url) VALUES (%s, %s)",
            (name, url)
        )
        conn.commit()
        site_id = cursor.lastrowid
    except Exception as e:
        conn.rollback()
        cursor.close()
        conn.close()
        return jsonify({"error": str(e)}), 400
    cursor.close()
    conn.close()
    return jsonify({"status": "registered", "id": site_id})
