import os
import re

base_dir = r"e:\_free downloader Projext"

# ============================================================
# PART 1: Comment out ALL ads.js files entirely
# ============================================================
ads_js_dirs = ['yt_d', 'tik_d', 'fb_downloader', 'insta_d', 'p_d', 'free_d']

for d in ads_js_dirs:
    ads_path = os.path.join(base_dir, d, 'static', 'js', 'ads.js')
    if not os.path.exists(ads_path):
        continue
    with open(ads_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if content.strip().startswith('// AD SCRIPT DISABLED'):
        print(f"  [SKIP] {ads_path} already disabled")
        continue
    
    # Comment out the entire file
    lines = content.split('\n')
    commented = '\n'.join([f'// AD SCRIPT DISABLED {line}' for line in lines])
    with open(ads_path, 'w', encoding='utf-8') as f:
        f.write(commented)
    print(f"  [DONE] Commented out {ads_path}")


# ============================================================
# PART 2: Comment out ad logic in script.js files
# ============================================================
script_js_files = [
    os.path.join(base_dir, 'fb_downloader', 'static', 'js', 'script.js'),
    os.path.join(base_dir, 'insta_d', 'static', 'js', 'script.js'),
    os.path.join(base_dir, 'p_d', 'static', 'js', 'script.js'),
]

for path in script_js_files:
    if not os.path.exists(path):
        continue
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original = content
    
    # Comment out Direct Link Ad block in handleDownloadClick
    content = re.sub(
        r'(            // 1\. Open Direct Link Ad in new tab\r?\n'
        r'            if \(window\.AD_CONFIG && window\.AD_CONFIG\.DIRECT_LINK_URL\.includes\("http"\)\) \{\r?\n'
        r'                window\.open\(window\.AD_CONFIG\.DIRECT_LINK_URL, \'_blank\'\);\r?\n'
        r'            \})',
        lambda m: '\n'.join(['// AD SCRIPT DISABLED ' + line for line in m.group(1).split('\n')]),
        content
    )
    
    # Comment out Pop-Under logic block
    content = re.sub(
        r'(        // --- POP-UNDER / ON-CLICK AD LOGIC ---\r?\n'
        r'        let popUnderTriggered = false;.*?'
        r'        document\.addEventListener\(\'paste\', triggerPopUnder, \{ capture: true \}\);)',
        lambda m: '\n'.join(['// AD SCRIPT DISABLED ' + line for line in m.group(1).split('\n')]),
        content,
        flags=re.DOTALL
    )
    
    if content != original:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  [DONE] Commented out ad logic in {path}")
    else:
        print(f"  [SKIP] {path} no changes needed")


# ============================================================
# PART 3: Fix remaining inline ad logic in TikTok index.html
# ============================================================

tik_html = os.path.join(base_dir, 'tik_d', 'templates', 'index.html')
if os.path.exists(tik_html):
    with open(tik_html, 'r', encoding='utf-8') as f:
        content = f.read()
    original = content
    
    # Comment out the openAdAndDownload direct link section
    content = re.sub(
        r'(        // --- DIRECT LINK AD & DOWNLOAD ---\r?\n'
        r'        function openAdAndDownload\(downloadUrl\) \{\r?\n'
        r'            if \(window\.AD_CONFIG && window\.AD_CONFIG\.DIRECT_LINK_URL\.includes\("http"\)\) \{\r?\n'
        r'                window\.open\(window\.AD_CONFIG\.DIRECT_LINK_URL, \'_blank\'\);\r?\n'
        r'            \})',
        lambda m: '\n'.join(['// AD SCRIPT DISABLED ' + line for line in m.group(1).split('\n')]),
        content
    )
    
    if content != original:
        with open(tik_html, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  [DONE] Commented out TikTok inline ad logic")
    else:
        print(f"  [SKIP] TikTok inline ad logic already handled")

# ============================================================
# PART 4: Fix remaining inline ad logic in p_d index.html
# ============================================================

pd_html = os.path.join(base_dir, 'p_d', 'templates', 'index.html')
if os.path.exists(pd_html):
    with open(pd_html, 'r', encoding='utf-8') as f:
        content = f.read()
    original = content
    
    # Comment out the Direct Link Ad open block
    content = re.sub(
        r'(        // Open Direct Link Ad in new tab\r?\n'
        r'        if \(window\.AD_CONFIG && window\.AD_CONFIG\.DIRECT_LINK_URL && window\.AD_CONFIG\.DIRECT_LINK_URL\.includes\("http"\)\) \{\r?\n'
        r'            window\.open\(window\.AD_CONFIG\.DIRECT_LINK_URL, \'_blank\'\);\r?\n'
        r'        \})',
        lambda m: '\n'.join(['// AD SCRIPT DISABLED ' + line for line in m.group(1).split('\n')]),
        content
    )
    
    if content != original:
        with open(pd_html, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  [DONE] Commented out p_d inline ad logic")
    else:
        print(f"  [SKIP] p_d inline ad logic already handled")


# ============================================================
# PART 5: Remove google-adsense-account and monetag meta tags
# from all index.html templates
# ============================================================

all_html_dirs = ['freeStore', 'fb_downloader', 'yt_d', 'tik_d', 'insta_d', 'p_d']
for d in all_html_dirs:
    html_path = os.path.join(base_dir, d, 'templates', 'index.html')
    if not os.path.exists(html_path):
        continue
    with open(html_path, 'r', encoding='utf-8') as f:
        content = f.read()
    original = content
    
    # Comment out google-adsense meta
    content = re.sub(
        r'(\s*<meta name="google-adsense-account" content="[^"]*">)',
        r'\n    <!-- AD SCRIPT DISABLED \1 -->',
        content
    )
    # Comment out monetag meta
    content = re.sub(
        r'(\s*<meta name="monetag" content="[^"]*">)',
        r'\n    <!-- AD SCRIPT DISABLED \1 -->',
        content
    )
    
    if content != original:
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  [DONE] Removed adsense/monetag meta from {html_path}")
    else:
        print(f"  [SKIP] {html_path} meta already handled")

print("\n=== ALL AD SCRIPTS FULLY DISABLED ===")
