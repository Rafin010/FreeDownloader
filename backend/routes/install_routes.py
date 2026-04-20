from flask import Blueprint, request, jsonify
from utils.db import get_connection

install_bp = Blueprint('install', __name__)

# ─────────────────────────────────────────────
# POST /api/install/register
# ─────────────────────────────────────────────
@install_bp.route('/register', methods=['POST'])
def register_install():
    data = request.get_json(silent=True) or {}
    install_id = data.get('install_id')
    user_id = data.get('user_id')
    software_name = data.get('software_name')
    
    if not all([install_id, user_id, software_name]):
        return jsonify({"error": "Missing required fields"}), 400
        
    conn = get_connection()
    if not conn:
        return jsonify({"error": "Database unavailable"}), 500
        
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO software_installs 
            (install_id, user_id, software_name, app_version, os_type, os_version, device_id, is_active)
            VALUES (%s, %s, %s, %s, %s, %s, %s, TRUE)
            ON DUPLICATE KEY UPDATE 
            is_active = TRUE, uninstalled_at = NULL, last_heartbeat = CURRENT_TIMESTAMP
        """, (
            install_id, user_id, software_name, 
            data.get('app_version'), data.get('os_type'), 
            data.get('os_version'), data.get('device_id')
        ))
        conn.commit()
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 400
    finally:
        cursor.close()
        conn.close()
        
    return jsonify({"status": "registered"})

# ─────────────────────────────────────────────
# POST /api/install/heartbeat
# ─────────────────────────────────────────────
@install_bp.route('/heartbeat', methods=['POST'])
def heartbeat():
    data = request.get_json(silent=True) or {}
    install_id = data.get('install_id')
    
    if not install_id:
        return jsonify({"error": "Missing install_id"}), 400
        
    conn = get_connection()
    if not conn:
        return jsonify({"error": "Database unavailable"}), 500
        
    cursor = conn.cursor()
    try:
        # Just update last heartbeat, restore active if they previously uninstalled
        cursor.execute("""
            UPDATE software_installs
            SET is_active = TRUE, uninstalled_at = NULL, last_heartbeat = CURRENT_TIMESTAMP
            WHERE install_id = %s
        """, (install_id,))
        conn.commit()
    except Exception as e:
        pass
    finally:
        cursor.close()
        conn.close()
        
    return jsonify({"status": "ok"})

# ─────────────────────────────────────────────
# POST /api/install/uninstall
# ─────────────────────────────────────────────
@install_bp.route('/uninstall', methods=['POST'])
def uninstall():
    data = request.get_json(silent=True) or {}
    install_id = data.get('install_id')
    
    if not install_id:
        return jsonify({"error": "Missing install_id"}), 400
        
    conn = get_connection()
    if not conn:
        return jsonify({"error": "Database unavailable"}), 500
        
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE software_installs
            SET is_active = FALSE, uninstalled_at = CURRENT_TIMESTAMP
            WHERE install_id = %s
        """, (install_id,))
        conn.commit()
    except Exception as e:
        pass
    finally:
        cursor.close()
        conn.close()
        
    return jsonify({"status": "uninstalled"})

# ─────────────────────────────────────────────
# Admin Endpoints
# ─────────────────────────────────────────────
@install_bp.route('/stats', methods=['GET'])
def get_stats():
    conn = get_connection()
    if not conn:
        return jsonify({"error": "Database unavailable"}), 500
        
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT software_name, 
               COUNT(*) as total_installs,
               SUM(CASE WHEN is_active = TRUE THEN 1 ELSE 0 END) as active_installs
        FROM software_installs
        GROUP BY software_name
    """)
    stats = cursor.fetchall()
    
    cursor.execute("SELECT COUNT(*) as total_active FROM software_installs WHERE is_active = TRUE")
    total = cursor.fetchone()['total_active']
    
    cursor.close()
    conn.close()
    
    return jsonify({"breakdown": stats, "total_active": total})
