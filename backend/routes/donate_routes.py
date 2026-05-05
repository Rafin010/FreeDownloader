from flask import Blueprint, request, jsonify, session
from utils.db import get_connection

donate_bp = Blueprint('donate_bp', __name__)

@donate_bp.route('/record', methods=['POST', 'OPTIONS'])
def record_donation():
    if request.method == 'OPTIONS':
        return '', 200
        
    data = request.json or {}
    amount = data.get('amount')
    currency = data.get('currency', 'USD')
    method = data.get('method', 'unknown')
    status = data.get('status', 'initiated')
    
    # Optional fields
    donor_name = data.get('name', 'Anonymous')
    trx_id = data.get('trx_id', '')
    sender = data.get('sender', '')
    
    if not amount:
        return jsonify({'error': 'Amount is required'}), 400

    conn = get_connection()
    if conn:
        cursor = conn.cursor()
        try:
            # Ensure columns exist (safe ALTER)
            try:
                cursor.execute("ALTER TABLE donations ADD COLUMN trx_id VARCHAR(100) DEFAULT ''")
            except:
                pass
            try:
                cursor.execute("ALTER TABLE donations ADD COLUMN sender VARCHAR(50) DEFAULT ''")
            except:
                pass
            conn.commit()

            cursor.execute("""
                INSERT INTO donations (amount, currency, payment_method, payment_status, donor_name, trx_id, sender)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (amount, currency, method, status, donor_name, trx_id, sender))
            conn.commit()
            return jsonify({'success': True, 'id': cursor.lastrowid})
        except Exception as e:
            print("[DONATE ERROR]", e)
            return jsonify({'error': str(e)}), 500
        finally:
            cursor.close()
            conn.close()
    return jsonify({'error': 'DB connection failed'}), 500

@donate_bp.route('/stats', methods=['GET'])
def get_stats():
    if not session.get('logged_in'):
        return jsonify({'error': 'Unauthorized'}), 401
        
    conn = get_connection()
    if conn:
        cursor = conn.cursor(dictionary=True)
        try:
            # Aggregate stats
            cursor.execute("""
                SELECT 
                    SUM(CASE WHEN currency='USD' THEN amount ELSE 0 END) as total_usd,
                    SUM(CASE WHEN currency='BDT' THEN amount ELSE 0 END) as total_bdt,
                    SUM(CASE WHEN currency NOT IN ('USD', 'BDT') THEN amount ELSE 0 END) as total_crypto,
                    COUNT(id) as total_donations
                FROM donations
            """)
            totals = cursor.fetchone()

            # Method breakdown
            cursor.execute("""
                SELECT payment_method, currency, SUM(amount) as total_amount, COUNT(id) as count
                FROM donations
                GROUP BY payment_method, currency
                ORDER BY count DESC
            """)
            methods = cursor.fetchall()
            
            # Recent donations
            cursor.execute("""
                SELECT id, amount, currency, payment_method, donor_name, payment_status, 
                       IFNULL(trx_id, '') as trx_id, IFNULL(sender, '') as sender,
                       DATE_FORMAT(created_at, '%%Y-%%m-%%d %%H:%%i') as date
                FROM donations 
                ORDER BY created_at DESC 
                LIMIT 50
            """)
            recent = cursor.fetchall()

            return jsonify({
                'totals': totals,
                'methods': methods,
                'recent': recent
            })
        except Exception as e:
            print("[DONATE STATS ERROR]", e)
            return jsonify({'error': str(e)}), 500
        finally:
            cursor.close()
            conn.close()
    return jsonify({'error': 'DB Error'}), 500
