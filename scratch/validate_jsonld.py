import re
import json
import os

def check_html(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        html = f.read()

    scripts = re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.DOTALL)
    
    faq_count = 0
    
    for i, script in enumerate(scripts):
        try:
            data = json.loads(script)
            if data.get('@type') == 'FAQPage':
                faq_count += 1
            if isinstance(data, list):
                for item in data:
                    if item.get('@type') == 'FAQPage':
                        faq_count += 1
        except Exception as e:
            pass
            
    if faq_count > 1:
        print(f"{filepath} has {faq_count} FAQPage schemas! (ERROR)")
        
    # Check for duplicate key in the JSON string itself
    for i, script in enumerate(scripts):
        # Count occurrences of "@type": "FAQPage" in the raw text
        raw_count = script.count('"@type": "FAQPage"') + script.count('"@type":"FAQPage"')
        if raw_count > 1:
             print(f"{filepath} has Duplicate '@type': 'FAQPage' keys in the same script! Raw count: {raw_count}")

base_dir = r'e:\_free downloader Projext'
for root, dirs, files in os.walk(base_dir):
    if 'venv' in root or '.git' in root or 'node_modules' in root:
        continue
    for file in files:
        if file.endswith('.html'):
            check_html(os.path.join(root, file))

print("Done scanning.")
