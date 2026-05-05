"""
Popup Config Routes — Controls donation popup toggle & notification broadcast.
Used by the donate-popup.js widget on all platform sites.
"""
from flask import Blueprint, request, jsonify
from utils.db import get_connection
import json

popup_config_bp = Blueprint('popup_config', __name__)


def _ensure_config_table():
    """Create the popup_config table if it doesn't exist."""
    conn = get_connection()
    if not conn:
        return
    cursor = conn.cursor()
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS popup_config (
                id INT PRIMARY KEY DEFAULT 1,
                donate_popup_enabled BOOLEAN DEFAULT TRUE,
                notification_id VARCHAR(100) DEFAULT NULL,
                notification_title VARCHAR(255) DEFAULT NULL,
                notification_message TEXT DEFAULT NULL,
                notification_button_text VARCHAR(100) DEFAULT NULL,
                notification_button_url VARCHAR(500) DEFAULT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )
        """)
        # Insert default row if empty
        cursor.execute("SELECT COUNT(*) as c FROM popup_config")
        row = cursor.fetchone()
        if row[0] == 0:
            cursor.execute("INSERT INTO popup_config (id, donate_popup_enabled) VALUES (1, TRUE)")
        conn.commit()

        # Add new columns if they don't exist
        try:
            cursor.execute("ALTER TABLE popup_config ADD COLUMN donate_popup_mode VARCHAR(50) DEFAULT 'all_time'")
            cursor.execute("ALTER TABLE popup_config ADD COLUMN donate_popup_start_day INT DEFAULT 1")
            cursor.execute("ALTER TABLE popup_config ADD COLUMN donate_popup_end_day INT DEFAULT 3")
            cursor.execute("ALTER TABLE popup_config ADD COLUMN donate_push_id VARCHAR(100) DEFAULT NULL")
            conn.commit()
        except Exception:
            pass

    except Exception as e:
        print(f"[POPUP CONFIG TABLE] {e}")
    finally:
        cursor.close()
        conn.close()


# ─────────────────────────────────────────────
# GET /api/popup/config — Public endpoint for widget
# ─────────────────────────────────────────────
@popup_config_bp.route('/config', methods=['GET', 'OPTIONS'])
def get_config():
    if request.method == 'OPTIONS':
        resp = jsonify({})
        resp.headers['Access-Control-Allow-Origin'] = '*'
        resp.headers['Access-Control-Allow-Methods'] = 'GET'
        return resp, 200

    _ensure_config_table()
    conn = get_connection()
    if not conn:
        return jsonify({'donate_popup_enabled': True, 'notification': None}), 200

    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM popup_config WHERE id = 1")
    cfg = cursor.fetchone()
    cursor.close()
    conn.close()

    if not cfg:
        return jsonify({'donate_popup_enabled': True, 'notification': None}), 200

    result = {
        'donate_popup_enabled': bool(cfg.get('donate_popup_enabled', True)),
        'donate_popup_mode': cfg.get('donate_popup_mode', 'all_time'),
        'donate_popup_start_day': cfg.get('donate_popup_start_day', 1),
        'donate_popup_end_day': cfg.get('donate_popup_end_day', 3),
        'donate_push_id': cfg.get('donate_push_id'),
        'notification': None,
    }

    # Include notification if set
    if cfg.get('notification_id') and cfg.get('notification_message'):
        result['notification'] = {
            'id': cfg['notification_id'],
            'title': cfg.get('notification_title', 'Notification'),
            'message': cfg['notification_message'],
            'button_text': cfg.get('notification_button_text'),
            'button_url': cfg.get('notification_button_url'),
        }

    resp = jsonify(result)
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp


# ─────────────────────────────────────────────
# POST /api/popup/config/toggle — Admin: Toggle donate popup
# ─────────────────────────────────────────────
@popup_config_bp.route('/config/toggle', methods=['POST'])
def toggle_donate_popup():
    _ensure_config_table()
    data = request.get_json(silent=True) or {}
    
    conn = get_connection()
    if not conn:
        return jsonify({'error': 'DB error'}), 500

    cursor = conn.cursor()
    try:
        if 'mode' in data:
            mode = data['mode']
            start_day = data.get('start_day', 1)
            end_day = data.get('end_day', 3)
            cursor.execute("""
                UPDATE popup_config 
                SET donate_popup_mode = %s, donate_popup_start_day = %s, donate_popup_end_day = %s 
                WHERE id = 1
            """, (mode, start_day, end_day))
            conn.commit()
            return jsonify({'success': True, 'mode': mode})
        elif 'push' in data:
            import uuid
            push_id = f"push-{uuid.uuid4().hex[:8]}"
            cursor.execute("UPDATE popup_config SET donate_push_id = %s WHERE id = 1", (push_id,))
            conn.commit()
            return jsonify({'success': True, 'push_id': push_id})
        else:
            # Legacy toggle
            enabled = data.get('enabled', True)
            mode = 'all_time' if enabled else 'off'
            cursor.execute("UPDATE popup_config SET donate_popup_enabled = %s, donate_popup_mode = %s WHERE id = 1", (enabled, mode))
            conn.commit()
            return jsonify({'success': True, 'donate_popup_enabled': enabled})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


# ─────────────────────────────────────────────
# POST /api/popup/config/notification — Admin: Send/clear notification
# ─────────────────────────────────────────────
@popup_config_bp.route('/config/notification', methods=['POST'])
def set_notification():
    _ensure_config_table()
    data = request.get_json(silent=True) or {}

    conn = get_connection()
    if not conn:
        return jsonify({'error': 'DB error'}), 500

    cursor = conn.cursor()
    try:
        if data.get('clear'):
            # Clear the notification
            cursor.execute("""
                UPDATE popup_config SET 
                    notification_id = NULL,
                    notification_title = NULL,
                    notification_message = NULL,
                    notification_button_text = NULL,
                    notification_button_url = NULL
                WHERE id = 1
            """)
            conn.commit()
            return jsonify({'success': True, 'message': 'Notification cleared'})
        else:
            import uuid
            notif_id = f"notif-{uuid.uuid4().hex[:8]}"
            cursor.execute("""
                UPDATE popup_config SET 
                    notification_id = %s,
                    notification_title = %s,
                    notification_message = %s,
                    notification_button_text = %s,
                    notification_button_url = %s
                WHERE id = 1
            """, (
                notif_id,
                data.get('title', 'Notification'),
                data.get('message', ''),
                data.get('button_text'),
                data.get('button_url'),
            ))
            conn.commit()
            return jsonify({'success': True, 'notification_id': notif_id})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


# ─────────────────────────────────────────────
# GET /api/popup/config/status — Admin: Get current status
# ─────────────────────────────────────────────
@popup_config_bp.route('/config/status', methods=['GET'])
def get_status():
    _ensure_config_table()
    conn = get_connection()
    if not conn:
        return jsonify({'error': 'DB error'}), 500

    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM popup_config WHERE id = 1")
    cfg = cursor.fetchone()
    cursor.close()
    conn.close()

    if cfg and cfg.get('updated_at'):
        cfg['updated_at'] = str(cfg['updated_at'])

    return jsonify(cfg or {})
