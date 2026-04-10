import os

apps = ['free_d', 'fb_downloader', 'yt_d', 'insta_d', 'tik_d']

ad_script = '''
    <!-- Global Ad Scripts (Pop-under, Direct Link, Push Notification) placeholders -->
    <script>
        // TODO: Insert Pop-under Ad Script here
        // TODO: Insert Direct Link Ad here
        // TODO: Insert Push Notification Script here
    </script>
'''

about_us_link = '<li><a href="/about" class="text-gray-400 hover:text-blue-400 transition-colors duration-300">About Us</a></li>'
privacy_line = '<li><a href="/privacy" class="text-gray-400 hover:text-blue-400 transition-colors duration-300">Privacy Policy</a></li>'

for app in apps:
    path = os.path.join(app, 'templates', 'index.html')
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        changed = False
        if '<!-- Global Ad Scripts' not in content:
            content = content.replace('</head>', ad_script + '</head>')
            changed = True
        
        if app != 'free_d' and 'About Us' not in content:
            if privacy_line in content:
                content = content.replace(privacy_line, about_us_link + '\n                ' + privacy_line)
                changed = True
        
        if changed:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f'{app} updated successfully.')
