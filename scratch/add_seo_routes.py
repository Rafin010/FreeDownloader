import os

apps = [
    r"e:\_free downloader Projext\yt_d\app.py",
    r"e:\_free downloader Projext\fb_downloader\app.py",
    r"e:\_free downloader Projext\tik_d\app.py",
    r"e:\_free downloader Projext\insta_d\app.py",
    r"e:\_free downloader Projext\p_d\app.py",
    r"e:\_free downloader Projext\free_d\app.py",
    r"e:\_free downloader Projext\freeStore\app.py"
]

route_code = """
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
"""

for app_path in apps:
    if os.path.exists(app_path):
        with open(app_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Avoid duplicate routes
        if "def serve_sitemap" not in content:
            # We want to insert it before the if __name__ == '__main__': block
            if "if __name__ == '__main__':" in content:
                content = content.replace("if __name__ == '__main__':", route_code + "\nif __name__ == '__main__':")
            else:
                content += "\n" + route_code
            
            with open(app_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Added SEO routes to {app_path}")
        else:
            print(f"Routes already exist in {app_path}")

