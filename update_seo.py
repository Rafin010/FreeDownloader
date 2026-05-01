import os
import csv
import re

csv_files = {
    'free_d': r'C:\Users\Rafin\.gemini\antigravity\brain\80f2b3ac-8466-490b-8c5a-796dfb0ae5ba\.system_generated\steps\1095\content.md',
    'fb_downloader': r'C:\Users\Rafin\.gemini\antigravity\brain\80f2b3ac-8466-490b-8c5a-796dfb0ae5ba\.system_generated\steps\1112\content.md',
    'tik_d': r'C:\Users\Rafin\.gemini\antigravity\brain\80f2b3ac-8466-490b-8c5a-796dfb0ae5ba\.system_generated\steps\1113\content.md',
    'yt_d': r'C:\Users\Rafin\.gemini\antigravity\brain\80f2b3ac-8466-490b-8c5a-796dfb0ae5ba\.system_generated\steps\1114\content.md',
    'insta_d': r'C:\Users\Rafin\.gemini\antigravity\brain\80f2b3ac-8466-490b-8c5a-796dfb0ae5ba\.system_generated\steps\1115\content.md'
}

def extract_top_keywords(csv_path, top_n=60):
    keywords = []
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            start_idx = 0
            for i, line in enumerate(lines):
                if line.startswith('"Keyword Text') or line.startswith('Keyword Text'):
                    start_idx = i + 1
                    break
            
            for line in lines[start_idx:]:
                line = line.strip()
                if not line:
                    continue
                # Remove starting and ending quotes if any
                if line.startswith('"'):
                    line = line[1:]
                if line.endswith('"'):
                    line = line[:-1]
                
                # The data is like: sex video downloader,LOW,0,74000,0.01,0.01
                parts = line.split(',')
                kw = parts[0].strip()
                if kw and kw.lower() != 'keyword text':
                    # sometimes keyword can have quotes if it was quoted
                    kw = kw.replace('"', '').strip()
                    keywords.append(kw)
                    if len(keywords) >= top_n:
                        break
    except Exception as e:
        print(f"Error reading {csv_path}: {e}")
    return keywords

for project, csv_path in csv_files.items():
    html_path = os.path.join(project, 'templates', 'index.html')
    if not os.path.exists(html_path):
        print(f"File not found: {html_path}")
        continue
    
    kws = extract_top_keywords(csv_path, top_n=60)
    if not kws:
        print(f"No keywords found for {project}")
        continue
    
    kw_string = ", ".join(kws)
    print(f"[{project}] Top keywords extracted: {kw_string[:100]}...")
    
    with open(html_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    pattern = r'(<meta\s+name=["\']keywords["\']\s+content=["\'])(.*?)(["\']\s*>)'
    
    if re.search(pattern, content, re.IGNORECASE | re.DOTALL):
        new_content = re.sub(pattern, rf'\g<1>{kw_string}\g<3>', content, flags=re.IGNORECASE | re.DOTALL)
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Updated keywords in {html_path}")
