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
    cookie_id  = data.get('cookie_id', '').strip()

    if not session_id or not website_id:
        return jsonify({"error": "Missing session_id or website_id"}), 400

    conn = get_connection()
    if not conn:
        return jsonify({"error": "Database unavailable"}), 500

    cursor = conn.cursor()

    try:
        # Ensure session row exists (in case ping arrives before first event)
        ip = request.remote_addr
        ua = request.headers.get('User-Agent', '')
        cursor.execute("""
            INSERT IGNORE INTO sessions (session_id, website_id, ip_address, device_type, cookie_id)
            VALUES (%s, %s, %s, %s, %s)
        """, (session_id, website_id, ip, ua, cookie_id))

        cursor.execute("""
            INSERT INTO active_users (session_id, website_id, last_ping)
            VALUES (%s, %s, CURRENT_TIMESTAMP)
            ON DUPLICATE KEY UPDATE last_ping = CURRENT_TIMESTAMP
        """, (session_id, website_id))

        # Update user_cookies last_seen
        if cookie_id:
            cursor.execute("""
                INSERT INTO user_cookies (cookie_id, preferences, total_views, total_downloads)
                VALUES (%s, '{}', 0, 0)
                ON DUPLICATE KEY UPDATE last_seen = CURRENT_TIMESTAMP
            """, (cookie_id,))

        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"[PING ERROR] {e}")
    finally:
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
    cookie_id   = data.get('cookie_id', '').strip()
    preferences = data.get('preferences')               # dict of category prefs
    meta        = data.get('meta')                       # optional dict for extra info

    if not session_id or not website_id or not event_type:
        return jsonify({"error": "Missing required fields"}), 400

    if event_type not in ('page_view', 'download', 'ad_impression'):
        return jsonify({"error": "Invalid event_type"}), 400

    ip = request.remote_addr
    ua = request.headers.get('User-Agent', '')
    meta_json = json.dumps(meta) if meta else None
    prefs_json = json.dumps(preferences) if preferences else '{}'

    conn = get_connection()
    if not conn:
        return jsonify({"error": "Database unavailable"}), 500

    cursor = conn.cursor()

    try:
        # Upsert session (with cookie_id)
        cursor.execute("""
            INSERT IGNORE INTO sessions (session_id, website_id, ip_address, device_type, category, cookie_id)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (session_id, website_id, ip, ua, category, cookie_id))

        cursor.execute("""
            UPDATE sessions SET last_active = CURRENT_TIMESTAMP, cookie_id = %s WHERE session_id = %s
        """, (cookie_id, session_id))

        # Insert event (with cookie_id)
        cursor.execute("""
            INSERT INTO events (session_id, website_id, event_type, category, cookie_id, meta)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (session_id, website_id, event_type, category, cookie_id, meta_json))

        # Upsert user_cookies — store preferences and increment counters
        if cookie_id:
            if event_type == 'page_view':
                cursor.execute("""
                    INSERT INTO user_cookies (cookie_id, preferences, total_views, total_downloads)
                    VALUES (%s, %s, 1, 0)
                    ON DUPLICATE KEY UPDATE
                        preferences = %s,
                        total_views = total_views + 1,
                        last_seen = CURRENT_TIMESTAMP
                """, (cookie_id, prefs_json, prefs_json))
            elif event_type == 'download':
                cursor.execute("""
                    INSERT INTO user_cookies (cookie_id, preferences, total_views, total_downloads)
                    VALUES (%s, %s, 0, 1)
                    ON DUPLICATE KEY UPDATE
                        preferences = %s,
                        total_downloads = total_downloads + 1,
                        last_seen = CURRENT_TIMESTAMP
                """, (cookie_id, prefs_json, prefs_json))
            else:
                cursor.execute("""
                    INSERT INTO user_cookies (cookie_id, preferences, total_views, total_downloads)
                    VALUES (%s, %s, 0, 0)
                    ON DUPLICATE KEY UPDATE
                        preferences = %s,
                        last_seen = CURRENT_TIMESTAMP
                """, (cookie_id, prefs_json, prefs_json))

        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"[EVENT ERROR] {e}")
    finally:
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
