import os

template_dirs = [
    r'e:\_free downloader Projext\yt_d\templates\index.html',
    r'e:\_free downloader Projext\fb_downloader\templates\index.html',
    r'e:\_free downloader Projext\insta_d\templates\index.html',
    r'e:\_free downloader Projext\tik_d\templates\index.html',
    r'e:\_free downloader Projext\p_d\templates\index.html',
    r'e:\_free downloader Projext\free_d\templates\index.html',
    r'e:\_free downloader Projext\freeStore\templates\index.html',
]

popup_tag = '<script src="https://freedownloader.top/donate/static/donate-popup.js" defer></script>'

for filepath in template_dirs:
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if 'donate-popup.js' not in content:
            content = content.replace('</body>', popup_tag + '\n</body>')
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f'Added popup to: {filepath}')
        else:
            print(f'Already has popup: {filepath}')
    else:
        print(f'NOT FOUND: {filepath}')
