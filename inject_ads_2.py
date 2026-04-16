import os

directories = ['freeStore', 'fb_downloader', 'yt_d', 'tik_d', 'insta_d', 'p_d']
base_dir = r"e:\_free downloader Projext"

new_ad = '<script src="https://pl29169633.profitablecpmratenetwork.com/40/cf/15/40cf152bda6c66873fc6153fa9019423.js"></script>'

for d in directories:
    file_path = os.path.join(base_dir, d, 'templates', 'index.html')
    if not os.path.exists(file_path):
        continue
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    original_content = content
    
    if "40cf152bda6c66873fc6153fa9019423.js" not in content:
        if "61da42f06fe184577aa472af517e61c2.js" in content:
            content = content.replace(
                '<script src="https://pl29169631.profitablecpmratenetwork.com/61/da/42/61da42f06fe184577aa472af517e61c2.js"></script>',
                f'<script src="https://pl29169631.profitablecpmratenetwork.com/61/da/42/61da42f06fe184577aa472af517e61c2.js"></script>\n    {new_ad}'
            )
        else:
            content = content.replace('</head>', f'    {new_ad}\n</head>')

    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated {file_path}")
