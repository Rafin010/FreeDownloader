from flask import Blueprint, jsonify, request
from utils.db import get_connection

dashboard_bp = Blueprint('dashboard', __name__)

ACTIVE_WINDOW_SECONDS = 90  # user is "online" if pinged within 90s


# ─────────────────────────────────────────────
# GET /api/dashboard/summary
# Global aggregated totals — OR per-site if ?site=xxx
# ─────────────────────────────────────────────
@dashboard_bp.route('/summary', methods=['GET'])
def summary():
    site_filter = request.args.get('site')  # optional: filter by website_id

    conn = get_connection()
    if not conn:
        return jsonify({"error": "Database unavailable"}), 500
    cursor = conn.cursor(dictionary=True)

    if site_filter:
        # Per-site totals
        cursor.execute("""
            SELECT event_type, COUNT(*) AS total
            FROM events WHERE website_id = %s
            GROUP BY event_type
        """, (site_filter,))
    else:
        cursor.execute("""
            SELECT event_type, COUNT(*) AS total
            FROM events GROUP BY event_type
        """)
    totals = {r['event_type']: r['total'] for r in cursor.fetchall()}

    # Active users
    if site_filter:
        cursor.execute("""
            SELECT COUNT(*) AS online FROM active_users
            WHERE last_ping >= NOW() - INTERVAL %s SECOND AND website_id = %s
        """, (ACTIVE_WINDOW_SECONDS, site_filter))
    else:
        cursor.execute("""
            SELECT COUNT(*) AS online FROM active_users
            WHERE last_ping >= NOW() - INTERVAL %s SECOND
        """, (ACTIVE_WINDOW_SECONDS,))
    online = cursor.fetchone()['online']

    # Total unique sessions
    if site_filter:
        cursor.execute("SELECT COUNT(*) AS total FROM sessions WHERE website_id = %s", (site_filter,))
    else:
        cursor.execute("SELECT COUNT(*) AS total FROM sessions")
    total_sessions = cursor.fetchone()['total']

    # Total registered sites
    cursor.execute("SELECT COUNT(*) AS total FROM websites")
    total_sites = cursor.fetchone()['total']

    cursor.close()
    conn.close()

    return jsonify({
        "views":          totals.get('page_view', 0),
        "downloads":      totals.get('download', 0),
        "ad_impressions": totals.get('ad_impression', 0),
        "online_now":     online,
        "total_sessions": total_sessions,
        "total_sites":    total_sites
    })


# ─────────────────────────────────────────────
# GET /api/dashboard/sites
# Per-site breakdown (always all sites)
# ─────────────────────────────────────────────
@dashboard_bp.route('/sites', methods=['GET'])
def sites_breakdown():
    conn = get_connection()
    if not conn:
        return jsonify({"error": "Database unavailable"}), 500
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            w.id,
            w.name,
            w.url,
            COALESCE(SUM(CASE WHEN e.event_type = 'page_view'      THEN 1 ELSE 0 END), 0) AS views,
            COALESCE(SUM(CASE WHEN e.event_type = 'download'        THEN 1 ELSE 0 END), 0) AS downloads,
            COALESCE(SUM(CASE WHEN e.event_type = 'ad_impression'   THEN 1 ELSE 0 END), 0) AS ad_impressions,
            COUNT(DISTINCT e.session_id) AS sessions
        FROM websites w
        LEFT JOIN events e ON e.website_id = w.url
        GROUP BY w.id, w.name, w.url
        ORDER BY views DESC
    """)
    sites = cursor.fetchall()

    cursor.execute("""
        SELECT website_id, COUNT(*) AS online
        FROM active_users
        WHERE last_ping >= NOW() - INTERVAL %s SECOND
        GROUP BY website_id
    """, (ACTIVE_WINDOW_SECONDS,))
    online_map = {r['website_id']: r['online'] for r in cursor.fetchall()}

    cursor.close()
    conn.close()

    for s in sites:
        s['online_now'] = online_map.get(s['url'], 0)

    return jsonify(sites)


# ─────────────────────────────────────────────
# GET /api/dashboard/chart/daily?site=xxx
# Last 30 days — with optional site filter
# ─────────────────────────────────────────────
@dashboard_bp.route('/chart/daily', methods=['GET'])
def chart_daily():
    site_filter = request.args.get('site')
    conn = get_connection()
    if not conn:
        return jsonify({"error": "Database unavailable"}), 500
    cursor = conn.cursor(dictionary=True)

    if site_filter:
        cursor.execute("""
            SELECT DATE(created_at) AS day, event_type, COUNT(*) AS total
            FROM events
            WHERE created_at >= NOW() - INTERVAL 30 DAY AND website_id = %s
            GROUP BY day, event_type ORDER BY day ASC
        """, (site_filter,))
    else:
        cursor.execute("""
            SELECT DATE(created_at) AS day, event_type, COUNT(*) AS total
            FROM events
            WHERE created_at >= NOW() - INTERVAL 30 DAY
            GROUP BY day, event_type ORDER BY day ASC
        """)

    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    pivot = {}
    for r in rows:
        day = str(r['day'])
        pivot.setdefault(day, {"page_view": 0, "download": 0, "ad_impression": 0})
        pivot[day][r['event_type']] = r['total']

    labels = sorted(pivot.keys())
    return jsonify({
        "labels":         labels,
        "page_views":     [pivot[d].get('page_view', 0) for d in labels],
        "downloads":      [pivot[d].get('download', 0) for d in labels],
        "ad_impressions": [pivot[d].get('ad_impression', 0) for d in labels]
    })


# ─────────────────────────────────────────────
# GET /api/dashboard/chart/hourly?site=xxx
# Last 24 hours — with optional site filter
# ─────────────────────────────────────────────
@dashboard_bp.route('/chart/hourly', methods=['GET'])
def chart_hourly():
    site_filter = request.args.get('site')
    conn = get_connection()
    if not conn:
        return jsonify({"error": "Database unavailable"}), 500
    cursor = conn.cursor(dictionary=True)

    if site_filter:
        cursor.execute("""
            SELECT DATE_FORMAT(created_at, '%%H:00') AS hour, event_type, COUNT(*) AS total
            FROM events
            WHERE created_at >= NOW() - INTERVAL 24 HOUR AND website_id = %s
            GROUP BY hour, event_type ORDER BY hour ASC
        """, (site_filter,))
    else:
        cursor.execute("""
            SELECT DATE_FORMAT(created_at, '%%H:00') AS hour, event_type, COUNT(*) AS total
            FROM events
            WHERE created_at >= NOW() - INTERVAL 24 HOUR
            GROUP BY hour, event_type ORDER BY hour ASC
        """)

    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    pivot = {}
    for r in rows:
        h = r['hour']
        pivot.setdefault(h, {"page_view": 0, "download": 0, "ad_impression": 0})
        pivot[h][r['event_type']] = r['total']

    labels = sorted(pivot.keys())
    return jsonify({
        "labels":         labels,
        "page_views":     [pivot[h].get('page_view', 0) for h in labels],
        "downloads":      [pivot[h].get('download', 0) for h in labels],
        "ad_impressions": [pivot[h].get('ad_impression', 0) for h in labels]
    })


# ─────────────────────────────────────────────
# GET /api/dashboard/top-events?site=xxx
# Event type distribution — with optional site filter
# ─────────────────────────────────────────────
@dashboard_bp.route('/top-events', methods=['GET'])
def top_events():
    site_filter = request.args.get('site')
    conn = get_connection()
    if not conn:
        return jsonify({"error": "Database unavailable"}), 500
    cursor = conn.cursor(dictionary=True)

    if site_filter:
        cursor.execute("""
            SELECT event_type, COUNT(*) AS total
            FROM events WHERE website_id = %s
            GROUP BY event_type ORDER BY total DESC
        """, (site_filter,))
    else:
        cursor.execute("""
            SELECT event_type, COUNT(*) AS total
            FROM events GROUP BY event_type ORDER BY total DESC
        """)

    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    return jsonify({
        "labels": [r['event_type'] for r in rows],
        "values": [r['total'] for r in rows]
    })


# ─────────────────────────────────────────────
# GET /api/dashboard/recent-sessions?site=xxx
# Last 50 sessions — with optional site filter
# ─────────────────────────────────────────────
@dashboard_bp.route('/recent-sessions', methods=['GET'])
def recent_sessions():
    site_filter = request.args.get('site')
    conn = get_connection()
    if not conn:
        return jsonify({"error": "Database unavailable"}), 500
    cursor = conn.cursor(dictionary=True)

    if site_filter:
        cursor.execute("""
            SELECT session_id, website_id, ip_address, device_type, category,
                   created_at, last_active
            FROM sessions WHERE website_id = %s
            ORDER BY last_active DESC LIMIT 50
        """, (site_filter,))
    else:
        cursor.execute("""
            SELECT session_id, website_id, ip_address, device_type, category,
                   created_at, last_active
            FROM sessions
            ORDER BY last_active DESC LIMIT 50
        """)

    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    for r in rows:
        r['created_at']  = str(r['created_at'])
        r['last_active'] = str(r['last_active'])
    return jsonify(rows)


# ─────────────────────────────────────────────
# GET /api/dashboard/cookie-stats
# Cookie-based user tracking analytics
# ─────────────────────────────────────────────
@dashboard_bp.route('/cookie-stats', methods=['GET'])
def cookie_stats():
    conn = get_connection()
    if not conn:
        return jsonify({"error": "Database unavailable"}), 500
    cursor = conn.cursor(dictionary=True)

    # Total unique tracked users
    cursor.execute("SELECT COUNT(*) AS total FROM user_cookies")
    total_users = cursor.fetchone()['total']

    # Users active in last 24h
    cursor.execute("""
        SELECT COUNT(*) AS active FROM user_cookies
        WHERE last_seen >= NOW() - INTERVAL 24 HOUR
    """)
    active_24h = cursor.fetchone()['active']

    # Users active in last 7 days
    cursor.execute("""
        SELECT COUNT(*) AS active FROM user_cookies
        WHERE last_seen >= NOW() - INTERVAL 7 DAY
    """)
    active_7d = cursor.fetchone()['active']

    # Top users by downloads
    cursor.execute("""
        SELECT cookie_id, total_views, total_downloads, preferences,
               first_seen, last_seen
        FROM user_cookies
        ORDER BY total_downloads DESC
        LIMIT 20
    """)
    top_users = cursor.fetchall()

    # Recent users
    cursor.execute("""
        SELECT cookie_id, total_views, total_downloads, preferences,
               first_seen, last_seen
        FROM user_cookies
        ORDER BY last_seen DESC
        LIMIT 50
    """)
    recent_users = cursor.fetchall()

    cursor.close()
    conn.close()

    # Convert datetimes and parse preferences
    import json
    for user_list in [top_users, recent_users]:
        for u in user_list:
            u['first_seen'] = str(u['first_seen'])
            u['last_seen']  = str(u['last_seen'])
            if u.get('preferences') and isinstance(u['preferences'], str):
                try:
                    u['preferences'] = json.loads(u['preferences'])
                except (json.JSONDecodeError, TypeError):
                    u['preferences'] = {}

    return jsonify({
        "total_tracked_users": total_users,
        "active_24h":          active_24h,
        "active_7d":           active_7d,
        "top_users":           top_users,
        "recent_users":        recent_users
    })
