from flask import Blueprint, request, jsonify, current_app, send_from_directory
from werkzeug.utils import secure_filename
from utils.db import get_connection
import os
import json

store_bp = Blueprint('store', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'zip', 'exe', 'msi', 'apk', 'dmg', 'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ─────────────────────────────────────────────
# GET /api/store/items
# ─────────────────────────────────────────────
@store_bp.route('/items', methods=['GET'])
def list_items():
    category = request.args.get('category')
    conn = get_connection()
    if not conn:
        return jsonify({"error": "Database unavailable"}), 500
    
    cursor = conn.cursor(dictionary=True)
    if category:
        cursor.execute("SELECT * FROM store_items WHERE category = %s AND is_active = TRUE ORDER BY created_at DESC", (category,))
    else:
        cursor.execute("SELECT * FROM store_items ORDER BY created_at DESC")
    
    items = cursor.fetchall()
    for item in items:
        if item.get('screenshots'):
            try:
                item['screenshots'] = json.loads(item['screenshots'])
            except:
                item['screenshots'] = []
        if item.get('system_requirements'):
            try:
                item['system_requirements'] = json.loads(item['system_requirements'])
            except:
                item['system_requirements'] = {}
        for key in ['created_at', 'updated_at']:
            if item.get(key):
                item[key] = str(item[key])
                
    cursor.close()
    conn.close()
    return jsonify(items)

# ─────────────────────────────────────────────
# GET /api/store/items/<slug>
# ─────────────────────────────────────────────
@store_bp.route('/items/<slug>', methods=['GET'])
def get_item(slug):
    conn = get_connection()
    if not conn:
        return jsonify({"error": "Database unavailable"}), 500
    
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM store_items WHERE slug = %s", (slug,))
    item = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if not item:
        return jsonify({"error": "Item not found"}), 404
        
    if item.get('screenshots'):
        try:
            item['screenshots'] = json.loads(item['screenshots'])
        except:
            item['screenshots'] = []
    if item.get('system_requirements'):
        try:
            item['system_requirements'] = json.loads(item['system_requirements'])
        except:
            item['system_requirements'] = {}
    for key in ['created_at', 'updated_at']:
        if item.get(key):
            item[key] = str(item[key])
            
    return jsonify(item)

# ─────────────────────────────────────────────
# POST /api/store/items (Admin)
# ─────────────────────────────────────────────
@store_bp.route('/items', methods=['POST'])
def create_item():
    # Require admin authentication conceptually (omitted for brevity here, assume protected)
    data = request.json
    required = ['title', 'slug', 'category']
    if not all(k in data for k in required):
        return jsonify({"error": "Missing required fields"}), 400
        
    conn = get_connection()
    if not conn:
        return jsonify({"error": "Database unavailable"}), 500
        
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO store_items (
                title, slug, category, developer, description, long_description,
                version, rating, price, download_link, file_path, file_size, 
                icon_url, screenshots, system_requirements
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            data.get('title'), data.get('slug'), data.get('category'),
            data.get('developer', 'Ifat Ahmed Rafin'), data.get('description'),
            data.get('long_description'), data.get('version', '1.0.0'),
            data.get('rating', 0.0), data.get('price', 'Free'),
            data.get('download_link'), data.get('file_path'), data.get('file_size'),
            data.get('icon_url'), json.dumps(data.get('screenshots', [])),
            json.dumps(data.get('system_requirements', {}))
        ))
        conn.commit()
        item_id = cursor.lastrowid
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 400
    finally:
        cursor.close()
        conn.close()
        
    return jsonify({"status": "created", "id": item_id})

# ─────────────────────────────────────────────
# PUT /api/store/items/<id> (Admin)
# ─────────────────────────────────────────────
@store_bp.route('/items/<int:item_id>', methods=['PUT'])
def update_item(item_id):
    data = request.json
    conn = get_connection()
    if not conn:
        return jsonify({"error": "Database unavailable"}), 500
    
    updates = []
    values = []
    
    for key in ['title', 'slug', 'category', 'developer', 'description', 'long_description', 
               'version', 'rating', 'price', 'download_link', 'file_path', 'file_size', 
               'icon_url', 'is_active']:
        if key in data:
            updates.append(f"{key} = %s")
            values.append(data[key])
            
    if 'screenshots' in data:
        updates.append("screenshots = %s")
        values.append(json.dumps(data['screenshots']))
        
    if 'system_requirements' in data:
        updates.append("system_requirements = %s")
        values.append(json.dumps(data['system_requirements']))
        
    if not updates:
        return jsonify({"error": "No fields to update"}), 400
        
    values.append(item_id)
    query = f"UPDATE store_items SET {', '.join(updates)} WHERE id = %s"
    
    cursor = conn.cursor()
    try:
        cursor.execute(query, values)
        conn.commit()
        updated = cursor.rowcount > 0
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 400
    finally:
        cursor.close()
        conn.close()
        
    return jsonify({"status": "updated" if updated else "not found"})

# ─────────────────────────────────────────────
# POST /api/store/upload (Admin)
# ─────────────────────────────────────────────
@store_bp.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    category = request.form.get('category', 'software')
    
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
        
    if category not in ['web', 'app', 'software']:
        return jsonify({"error": "Invalid category"}), 400
        
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        save_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], category)
        os.makedirs(save_dir, exist_ok=True)
        file_path = os.path.join(save_dir, filename)
        
        file.save(file_path)
        
        # Calculate size
        size_bytes = os.path.getsize(file_path)
        size_mb = round(size_bytes / (1024 * 1024), 2)
        
        # Public URL format assuming reverse proxy handles /uploads/
        public_url = f"/uploads/{category}/{filename}"
        
        return jsonify({
            "status": "success",
            "filename": filename,
            "path": public_url,
            "size": f"{size_mb} MB"
        })
        
    return jsonify({"error": "File type not allowed"}), 400

# ─────────────────────────────────────────────
# GET /api/store/download/<id> (Track & Serve)
# ─────────────────────────────────────────────
@store_bp.route('/download/<int:item_id>', methods=['GET'])
def download_item(item_id):
    conn = get_connection()
    if not conn:
        return jsonify({"error": "Database unavailable"}), 500
        
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT file_path, download_link FROM store_items WHERE id = %s", (item_id,))
    item = cursor.fetchone()
    
    if not item:
        cursor.close()
        conn.close()
        return jsonify({"error": "Item not found"}), 404
        
    # Increment download count
    cursor.execute("UPDATE store_items SET download_count = download_count + 1 WHERE id = %s", (item_id,))
    conn.commit()
    cursor.close()
    conn.close()
    
    if item['file_path']:
        # It's an uploaded file
        # file_path is something like /uploads/software/app.exe
        # For security, you might want to redirect instead, but here we can just redirect to the public URL
        return jsonify({"redirect": item['file_path']})
    elif item['download_link']:
        # External link
        return jsonify({"redirect": item['download_link']})
        
    return jsonify({"error": "No download associated"}), 404

# ─────────────────────────────────────────────
# DELETE /api/store/items/<id> (Admin)
# ─────────────────────────────────────────────
@store_bp.route('/items/<int:item_id>', methods=['DELETE'])
def delete_item(item_id):
    conn = get_connection()
    if not conn:
        return jsonify({"error": "Database unavailable"}), 500
    
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM store_items WHERE id = %s", (item_id,))
        conn.commit()
        deleted = cursor.rowcount > 0
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 400
    finally:
        cursor.close()
        conn.close()
        
    if deleted:
        return jsonify({"status": "deleted"})
    return jsonify({"error": "Item not found"}), 404

