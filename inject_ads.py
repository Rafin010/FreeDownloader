import os
import re

directories = ['freeStore', 'fb_downloader', 'yt_d', 'tik_d', 'insta_d', 'p_d']
base_dir = r"e:\_free downloader Projext"

ad_popunder = """<!-- Adsterra Popunder / Direct JS -->
    <script src="https://pl29169631.profitablecpmratenetwork.com/61/da/42/61da42f06fe184577aa472af517e61c2.js"></script>"""

ad_728 = """<div class="hidden md:flex justify-center my-6 w-full overflow-hidden">
<script>
  atOptions = {
    'key' : '769022bd3df750ba0e9c753489b4dabb',
    'format' : 'iframe',
    'height' : 90,
    'width' : 728,
    'params' : {}
  };
</script>
<script src="https://www.highperformanceformat.com/769022bd3df750ba0e9c753489b4dabb/invoke.js"></script>
</div>"""

ad_320 = """<div class="flex md:hidden justify-center my-4 w-full overflow-hidden">
<script>
  atOptions = {
    'key' : '697d33d8a1f05f7cc25386cb936cb90e',
    'format' : 'iframe',
    'height' : 50,
    'width' : 320,
    'params' : {}
  };
</script>
<script src="https://www.highperformanceformat.com/697d33d8a1f05f7cc25386cb936cb90e/invoke.js"></script>
</div>"""

ad_160 = """<div class="hidden xl:block fixed right-4 top-1/2 transform -translate-y-1/2 z-[100]">
<script>
  atOptions = {
    'key' : 'af22fee015371594b9f71002d68a9d72',
    'format' : 'iframe',
    'height' : 300,
    'width' : 160,
    'params' : {}
  };
</script>
<script src="https://www.highperformanceformat.com/af22fee015371594b9f71002d68a9d72/invoke.js"></script>
</div>"""

for d in directories:
    file_path = os.path.join(base_dir, d, 'templates', 'index.html')
    if not os.path.exists(file_path):
        print(f"Skipping {file_path}")
        continue

    print(f"Processing {file_path}")
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    original_content = content
    
    content = re.sub(r'<!-- Global Ad Scripts.*?</script>', '', content, flags=re.DOTALL | re.IGNORECASE)
    content = re.sub(r'<!-- Onclick Pop-under Ad.*?</script>', '', content, flags=re.DOTALL | re.IGNORECASE)
    content = re.sub(r'<!-- Push Notification Ad.*?</script>', '', content, flags=re.DOTALL | re.IGNORECASE)
    content = re.sub(r'<!-- Vignette Banner Ad.*?</script>', '', content, flags=re.DOTALL | re.IGNORECASE)
    
    # Tracker divs
    content = re.sub(r'<div class="tracker-ad".*?</div>', '', content)

    # Inject Popunder
    if "61da42f06fe184577aa472af517e61c2.js" not in content:
        content = content.replace('</head>', f'{ad_popunder}\n</head>')

    # Inject 728x90
    if "769022bd3df750ba0e9c753489b4dabb" not in content:
        # Check for placeholder first
        pattern_728 = r'<div[^>]*>[\s\n]*<p[^>]*>Advertisement</p>[\s\n]*<a[^>]*>[\s\n]*<img[^>]*728x90[^>]*>[\s\n]*</a>[\s\n]*</div>'
        if re.search(pattern_728, content):
            content = re.sub(pattern_728, ad_728.replace('\\', '\\\\'), content)
        else:
            pattern_728_alt = r'\[\s*Banner Ad Placement - 728x90\s*\]'
            if re.search(pattern_728_alt, content, flags=re.IGNORECASE):
                content = re.sub(pattern_728_alt, ad_728.replace('\\', '\\\\'), content, flags=re.IGNORECASE)
            else:
                if 'id="loading"' in content:
                    content = re.sub(r'(<div[^>]*id="loading"[^>]*>)', lambda m: f'{ad_728}\n{m.group(1)}', content)
                elif 'id="projectGrid"' in content: # FreeStore
                    content = content.replace('id="projectGrid">', f'id="projectGrid">\n{ad_728}')
                else:
                    content = content.replace('<footer', f'{ad_728}\n<footer')

    # Inject 320x50
    if "697d33d8a1f05f7cc25386cb936cb90e" not in content:
        if '<footer' in content:
            content = content.replace('<footer', f'{ad_320}\n<footer')
        else:
            content = content.replace('</body>', f'{ad_320}\n</body>')

    # Inject 160x300
    if "af22fee015371594b9f71002d68a9d72" not in content:
        content = content.replace('</body>', f'{ad_160}\n</body>')

    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated {file_path}")
    else:
        print(f"No changes needed for {file_path}")

print("Done injecting ads.")
