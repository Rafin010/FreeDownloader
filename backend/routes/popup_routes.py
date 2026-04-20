from flask import Blueprint, request, jsonify
from utils.db import get_connection
import json
import datetime

popup_bp = Blueprint('popup', __name__)

# ─────────────────────────────────────────────
# GET /api/popup/check
# ─────────────────────────────────────────────
@popup_bp.route('/check', methods=['GET'])
def check_popup():
    user_id = request.args.get('user_id')
    category = request.args.get('category')
    
    if not user_id:
        return jsonify({"error": "Missing user_id"}), 400
        
    conn = get_connection()
    if not conn:
        return jsonify({"error": "Database unavailable"}), 500
        
    cursor = conn.cursor(dictionary=True)
    
    # Simple logic: get active campaigns where category matches (or is null), ordered by priority
    query = """
        SELECT c.* FROM popup_campaigns c
        WHERE c.is_active = TRUE
        AND (c.category_filter IS NULL OR c.category_filter = %s OR c.category_filter = '')
        AND (c.start_date IS NULL OR c.start_date <= NOW())
        AND (c.end_date IS NULL OR c.end_date >= NOW())
        ORDER BY c.priority DESC
    """
    cursor.execute(query, (category,))
    campaigns = cursor.fetchall()
    
    target_campaign = None
    
    for campaign in campaigns:
        # Check schedule
        show_it = False
        if campaign['schedule_type'] == 'always':
            show_it = True
        elif campaign['schedule_type'] == 'dates':
            dates = json.loads(campaign['schedule_dates'] or '[]')
            today = datetime.date.today().day
            if today in dates:
                show_it = True
                
        # If it should be shown, check if user already saw it recently (e.g. today)
        if show_it:
            cursor.execute("""
                SELECT id FROM popup_interactions 
                WHERE campaign_id = %s AND user_id = %s AND DATE(created_at) = CURDATE()
            """, (campaign['id'], user_id))
            seen = cursor.fetchone()
            if not seen:
                target_campaign = campaign
                break
                
    cursor.close()
    conn.close()
    
    if target_campaign:
        # Avoid sending internal structure
        return jsonify({
            "id": target_campaign['id'],
            "title": target_campaign['title'],
            "message": target_campaign['message'],
            "type": target_campaign['popup_type'],
            "button_text": target_campaign['button_text'],
            "button_url": target_campaign['button_url']
        })
        
    return jsonify({"popup": None})

# ─────────────────────────────────────────────
# POST /api/popup/interact
# ─────────────────────────────────────────────
@popup_bp.route('/interact', methods=['POST'])
def log_interaction():
    data = request.get_json(silent=True) or {}
    campaign_id = data.get('campaign_id')
    user_id = data.get('user_id')
    action = data.get('action') # shown, clicked, dismissed
    
    if not all([campaign_id, user_id, action]):
        return jsonify({"error": "Missing fields"}), 400
        
    conn = get_connection()
    if not conn:
        return jsonify({"error": "Database unavailable"}), 500
        
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO popup_interactions (campaign_id, user_id, action)
            VALUES (%s, %s, %s)
        """, (campaign_id, user_id, action))
        
        # Increment counters on campaign
        if action == 'shown':
            cursor.execute("UPDATE popup_campaigns SET shown_count = shown_count + 1 WHERE id = %s", (campaign_id,))
        elif action == 'clicked':
            cursor.execute("UPDATE popup_campaigns SET click_count = click_count + 1 WHERE id = %s", (campaign_id,))
            
        conn.commit()
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 400
    finally:
        cursor.close()
        conn.close()
        
    return jsonify({"status": "ok"})

# ─────────────────────────────────────────────
# Admin Setup basic CRUD (omitted full logic for brevity, just listings)
# ─────────────────────────────────────────────
@popup_bp.route('/campaigns', methods=['GET'])
def get_campaigns():
    conn = get_connection()
    if not conn:
        return jsonify({"error": "Database unavailable"}), 500
        
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM popup_campaigns ORDER BY priority DESC, created_at DESC")
    campaigns = cursor.fetchall()
    
    for c in campaigns:
        for key in ['start_date', 'end_date', 'created_at', 'updated_at']:
            if c.get(key):
                c[key] = str(c[key])
                
    cursor.close()
    conn.close()
    return jsonify(campaigns)

@popup_bp.route('/campaigns', methods=['POST'])
def create_campaign():
    data = request.get_json(silent=True) or {}
    conn = get_connection()
    if not conn:
        return jsonify({"error": "Database unavailable"}), 500
        
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO popup_campaigns 
            (title, message, popup_type, button_text, button_url, category_filter, schedule_type, schedule_dates, priority)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            data.get('title'), data.get('message'), data.get('popup_type', 'donation'),
            data.get('button_text', 'Donate Now'), data.get('button_url'), data.get('category_filter'),
            data.get('schedule_type', 'always'), json.dumps(data.get('schedule_dates', [])),
            data.get('priority', 0)
        ))
        conn.commit()
        c_id = cursor.lastrowid
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 400
    finally:
        cursor.close()
        conn.close()
        
    return jsonify({"status": "created", "id": c_id})
