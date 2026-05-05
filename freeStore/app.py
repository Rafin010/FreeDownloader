import sys
import os
from flask import Flask, render_template, abort

# Add backend directory to sys.path to access utils/db.py
backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'backend')
if backend_dir not in sys.path:
    sys.path.append(backend_dir)

from utils.db import get_connection

app = Flask(__name__)

@app.route('/')
def home():
    conn = get_connection()
    if not conn:
        return "Database Error", 500
        
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM store_items WHERE is_active = TRUE ORDER BY created_at DESC")
    projects = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return render_template('index.html', projects=projects)

@app.route('/item/<slug>')
def item_detail(slug):
    conn = get_connection()
    if not conn:
        return "Database Error", 500
        
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM store_items WHERE slug = %s AND is_active = TRUE", (slug,))
    item = cursor.fetchone()
    
    if item:
        # Also fetch 3 related items to show at bottom
        cursor.execute("SELECT * FROM store_items WHERE category = %s AND id != %s AND is_active = TRUE LIMIT 3", (item['category'], item['id']))
        related = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    if not item:
        abort(404)
        
    import json
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
            
    return render_template('detail.html', item=item, related=related)

@app.route('/donate')
def donate():
    return render_template('donate.html')


@app.route('/sitemap.xml')
def serve_sitemap():
    import os
    from flask import send_from_directory
    return send_from_directory(os.path.dirname(os.path.abspath(__file__)), 'sitemap.xml')

@app.route('/robots.txt')
def serve_robots():
    import os
    from flask import send_from_directory
    return send_from_directory(os.path.dirname(os.path.abspath(__file__)), 'robots.txt')

if __name__ == '__main__':
    app.run(debug=True, port=8010)