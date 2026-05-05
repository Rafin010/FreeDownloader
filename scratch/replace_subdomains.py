import os

replacements = {
    "facebook.freedownloader.top": "f.freedownloader.top",
    "instagram.freedownloader.top": "i.freedownloader.top",
    "tiktok.freedownloader.top": "t.freedownloader.top",
    "youtube.freedownloader.top": "y.freedownloader.top",
    "porn.freedownloader.top": "p.freedownloader.top"
}

def replace_in_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        original_content = content
        
        for old, new in replacements.items():
            content = content.replace(old, new)
            
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Updated: {filepath}")
    except Exception as e:
        print(f"Failed to process {filepath}: {e}")

base_dir = r"e:\_free downloader Projext"
for root, dirs, files in os.walk(base_dir):
    if any(d in root for d in ['.git', 'venv', 'node_modules', '__pycache__', 'scratch']):
        continue
    for file in files:
        if file.endswith(('.html', '.py', '.js', '.conf', '.xml', '.txt', '.md')):
            replace_in_file(os.path.join(root, file))

print("All replacements done.")
