import os
import re
import glob

base_dir = r"e:\_free downloader Projext"
all_dirs = ['freeStore', 'fb_downloader', 'yt_d', 'tik_d', 'insta_d', 'p_d', 'free_d', 'backend']

count = 0

for d in all_dirs:
    template_dir = os.path.join(base_dir, d, 'templates')
    if not os.path.isdir(template_dir):
        continue
    
    for html_file in glob.glob(os.path.join(template_dir, '*.html')):
        with open(html_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original = content
        
        # 1. Comment out 5gvci.com Monetag Social Bar tag script
        content = re.sub(
            r'^(\s*<script src="https://5gvci\.com/act/files/tag\.min\.js\?z=\d+"[^>]*></script>)\s*$',
            r'    <!-- AD SCRIPT DISABLED \1 -->',
            content,
            flags=re.MULTILINE
        )
        
        # 2. Comment out any remaining monetag meta NOT already commented
        content = re.sub(
            r'^(\s*<meta name="monetag" content="[^"]*">)\s*$',
            r'    <!-- AD SCRIPT DISABLED \1 -->',
            content,
            flags=re.MULTILINE
        )
        
        # 3. Comment out any remaining google-adsense meta NOT already commented
        content = re.sub(
            r'^(\s*<meta name="google-adsense-account" content="[^"]*">)\s*$',
            r'    <!-- AD SCRIPT DISABLED \1 -->',
            content,
            flags=re.MULTILINE
        )
        
        if content != original:
            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(content)
            count += 1
            print(f"  [FIXED] {html_file}")

# 4. Disable the sw.js service worker file
sw_path = os.path.join(base_dir, 'fb_downloader', 'static', 'js', 'sw.js')
if os.path.exists(sw_path):
    with open(sw_path, 'r', encoding='utf-8') as f:
        content = f.read()
    if not content.strip().startswith('// AD SCRIPT DISABLED'):
        lines = content.split('\n')
        commented = '\n'.join([f'// AD SCRIPT DISABLED {line}' for line in lines])
        with open(sw_path, 'w', encoding='utf-8') as f:
            f.write(commented)
        count += 1
        print(f"  [FIXED] {sw_path} (Service Worker disabled)")

# 5. Check for sw.js in ALL other directories and disable
for d in all_dirs:
    for root, dirs, files in os.walk(os.path.join(base_dir, d)):
        for f in files:
            if f == 'sw.js':
                fp = os.path.join(root, f)
                if fp == sw_path:
                    continue
                with open(fp, 'r', encoding='utf-8') as fh:
                    c = fh.read()
                if not c.strip().startswith('// AD SCRIPT DISABLED'):
                    lines = c.split('\n')
                    commented = '\n'.join([f'// AD SCRIPT DISABLED {line}' for line in lines])
                    with open(fp, 'w', encoding='utf-8') as fh:
                        fh.write(commented)
                    count += 1
                    print(f"  [FIXED] {fp} (Service Worker disabled)")

print(f"\n=== Final cleanup complete: {count} files fixed ===")
