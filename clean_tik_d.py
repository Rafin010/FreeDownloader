import os
import re
import glob

base_dir = r"e:\_free downloader Projext\tik_d"

def remove_ad_comments(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    original = content

    # HTML comments for ads
    # Remove <!-- AD SCRIPT DISABLED --> blocks and any content inside it for meta/scripts
    content = re.sub(r'<!--\s*AD SCRIPT DISABLED\s*.*?-->', '', content, flags=re.DOTALL)
    
    # Remove any scripts matching profitablecpmratenetwork, highperformanceformat, 5gvci
    content = re.sub(r'<script[^>]*profitablecpmratenetwork[^>]*></script>', '', content)
    content = re.sub(r'<script[^>]*highperformanceformat[^>]*></script>', '', content)
    content = re.sub(r'<script[^>]*5gvci[^>]*></script>', '', content)

    # JS comments
    # Remove lines starting with // AD SCRIPT DISABLED
    lines = content.split('\n')
    lines = [line for line in lines if not line.strip().startswith('// AD SCRIPT DISABLED')]
    content = '\n'.join(lines)

    # Specific fix for index.html JS logic that was commented
    content = content.replace('// Attach the Ad function to the click event\n                    btn.onclick = () => openAdAndDownload(downloadUrl);', '                    btn.onclick = () => {\n                        const a = document.createElement(\'a\');\n                        a.style.display = \'none\';\n                        a.href = downloadUrl;\n                        a.download = \'\';\n                        document.body.appendChild(a);\n                        a.click();\n                        document.body.removeChild(a);\n                    };')
    
    if content != original:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Cleaned {file_path}")

# Process templates
for html_file in glob.glob(os.path.join(base_dir, 'templates', '*.html')):
    remove_ad_comments(html_file)

# Process JS
for js_file in glob.glob(os.path.join(base_dir, 'static', 'js', '*.js')):
    remove_ad_comments(js_file)

print("done")
