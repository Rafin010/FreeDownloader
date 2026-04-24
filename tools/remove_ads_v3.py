import os
import re
import glob

base_dir = r"e:\_free downloader Projext"
all_dirs = ['freeStore', 'fb_downloader', 'yt_d', 'tik_d', 'insta_d', 'p_d', 'free_d']

count = 0

for d in all_dirs:
    template_dir = os.path.join(base_dir, d, 'templates')
    if not os.path.isdir(template_dir):
        continue
    
    for html_file in glob.glob(os.path.join(template_dir, '*.html')):
        with open(html_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original = content
        
        # 1. Comment out monetag meta (not already in a comment)
        content = re.sub(
            r'^(\s*<meta name="monetag" content="[^"]*">)\s*$',
            r'    <!-- AD SCRIPT DISABLED \1 -->',
            content,
            flags=re.MULTILINE
        )
        
        # 2. Comment out google-adsense-account meta (not already in a comment)
        content = re.sub(
            r'^(\s*<meta name="google-adsense-account" content="[^"]*">)\s*$',
            r'    <!-- AD SCRIPT DISABLED \1 -->',
            content,
            flags=re.MULTILINE
        )
        
        # 3. Comment out <script src="/static/js/ads.js"></script> references
        content = re.sub(
            r'^(\s*<script src="/static/js/ads\.js"></script>)\s*$',
            r'    <!-- AD SCRIPT DISABLED \1 -->',
            content,
            flags=re.MULTILINE
        )
        
        if content != original:
            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(content)
            count += 1
            print(f"  [FIXED] {html_file}")

print(f"\n=== Fixed {count} files ===")
